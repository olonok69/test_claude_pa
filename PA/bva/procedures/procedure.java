package com.example;

import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Result;
import org.neo4j.graphdb.Transaction;
import org.neo4j.logging.Log;
import org.neo4j.procedure.*;

import java.util.*;
import java.util.stream.Stream;

/**
 * Neo4j stored procedure for session recommendations.
 * This procedure can be called directly from Cypher.
 */
public class SessionRecommendationProcedures {

    @Context
    public GraphDatabaseService db;

    @Context
    public Log log;

    /**
     * Recommends sessions for a visitor based on their profile.
     * 
     * @param badgeId The visitor's badge ID
     * @param assistYearBefore "1" if visitor attended last year, "0" otherwise
     * @param minScore Minimum similarity score (0.0-1.0)
     * @param maxRecommendations Maximum number of recommendations (null = no limit)
     * @param numSimilarVisitors Number of similar visitors to consider
     * @return Stream of recommended sessions
     */
    @Procedure(value = "com.example.recommendSessions", mode = Mode.READ)
    @Description("Recommends sessions for a visitor based on profile and history")
    public Stream<SessionRecommendation> recommendSessions(
            @Name("badgeId") String badgeId,
            @Name(value = "assistYearBefore", defaultValue = "1") String assistYearBefore,
            @Name(value = "minScore", defaultValue = "0.0") Double minScore,
            @Name(value = "maxRecommendations", defaultValue = "10") Long maxRecommendations,
            @Name(value = "numSimilarVisitors", defaultValue = "3") Long numSimilarVisitors) {

        List<SessionRecommendation> recommendations = new ArrayList<>();
        
        try (Transaction tx = db.beginTx()) {
            // Check if visitor exists
            String visitorQuery = "MATCH (v:Visitor_this_year {BadgeId: $badgeId}) RETURN v";
            Result visitorResult = tx.execute(visitorQuery, Map.of("badgeId", badgeId));
            
            if (!visitorResult.hasNext()) {
                log.warn("Visitor with BadgeId " + badgeId + " not found");
                return recommendations.stream();
            }
            
            List<String> pastSessionIds = new ArrayList<>();
            
            if ("1".equals(assistYearBefore)) {
                // Case 1: Visitor attended last year
                log.info("Case 1: Visitor " + badgeId + " attended last year");
                
                // Get sessions the visitor attended last year - FIXED to use only Sessions_past_year
                String pastSessionQuery = 
                    "MATCH (v:Visitor_this_year {BadgeId: $badgeId})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year) " +
                    "WHERE (vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva) " +
                    "RETURN sp.session_id AS sessionId";
                
                Result pastSessionResult = tx.execute(pastSessionQuery, Map.of("badgeId", badgeId));
                while (pastSessionResult.hasNext()) {
                    Map<String, Object> row = pastSessionResult.next();
                    pastSessionIds.add((String) row.get("sessionId"));
                }
            } else {
                // Case 2: New visitor - find similar visitors
                log.info("Case 2: Finding similar visitors for " + badgeId);
                
                // This part would ideally call your Python code for finding similar visitors
                // Here we're using a simpler approach with direct attribute matching
                String similarVisitorsQuery = 
                    "MATCH (visitor:Visitor_this_year {BadgeId: $badgeId}) " +
                    "MATCH (other:Visitor_this_year) " +
                    "WHERE other.BadgeId <> visitor.BadgeId AND other.assist_year_before = '1' " +
                    "WITH visitor, other, " +
                    "CASE WHEN visitor.job_role = other.job_role THEN 1 ELSE 0 END + " +
                    "CASE WHEN visitor.what_type_does_your_practice_specialise_in = other.what_type_does_your_practice_specialise_in THEN 1 ELSE 0 END + " +
                    "CASE WHEN visitor.organisation_type = other.organisation_type THEN 1 ELSE 0 END + " +
                    "CASE WHEN visitor.JobTitle = other.JobTitle THEN 1 ELSE 0 END + " +
                    "CASE WHEN visitor.Country = other.Country THEN 1 ELSE 0 END AS similarity " +
                    "ORDER BY similarity DESC " +
                    "LIMIT $numSimilarVisitors " +
                    "RETURN other.BadgeId AS similarVisitorId";
                
                Result similarVisitorsResult = tx.execute(similarVisitorsQuery, 
                    Map.of("badgeId", badgeId, "numSimilarVisitors", numSimilarVisitors));
                
                List<String> similarVisitorIds = new ArrayList<>();
                while (similarVisitorsResult.hasNext()) {
                    Map<String, Object> row = similarVisitorsResult.next();
                    similarVisitorIds.add((String) row.get("similarVisitorId"));
                }
                
                log.info("Similar visitors found: " + similarVisitorIds);
                
                if (!similarVisitorIds.isEmpty()) {
                    // Get sessions attended by similar visitors - FIXED to use only Sessions_past_year
                    String similarVisitorSessionsQuery = 
                        "MATCH (v:Visitor_this_year)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year) " +
                        "WHERE v.BadgeId IN $similarVisitorIds AND " +
                              "(vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva) " +
                        "RETURN DISTINCT sp.session_id AS sessionId";
                    
                    Result similarVisitorSessionsResult = tx.execute(similarVisitorSessionsQuery, 
                        Map.of("similarVisitorIds", similarVisitorIds));
                    
                    while (similarVisitorSessionsResult.hasNext()) {
                        Map<String, Object> row = similarVisitorSessionsResult.next();
                        pastSessionIds.add((String) row.get("sessionId"));
                    }
                }
            }
            
            log.info("Found " + pastSessionIds.size() + " past sessions");
            
            if (!pastSessionIds.isEmpty()) {
                // Get recommendations based on past sessions
                // Use stream matching for similarity calculation
                String recommendationsQuery = 
                    "MATCH (past:Sessions_past_year) " +  // FIXED to use only Sessions_past_year
                    "WHERE past.session_id IN $pastSessionIds " +
                    "MATCH (current:Sessions_this_year) " +
                    "WHERE current.stream IS NOT NULL AND past.stream IS NOT NULL " +
                    "WITH current, past, " +
                    "CASE WHEN current.stream = past.stream THEN 1.0 " +
                         "WHEN current.stream CONTAINS past.stream OR past.stream CONTAINS current.stream THEN 0.8 " +
                         "ELSE 0.5 END AS similarity " +
                    "WHERE similarity >= $minScore " +
                    "RETURN current.session_id AS sessionId, " +
                           "current.title AS title, " +
                           "current.stream AS stream, " +
                           "current.synopsis_stripped AS synopsis, " +
                           "current.date AS date, " +
                           "current.start_time AS startTime, " +
                           "current.end_time AS endTime, " +
                           "current.theatre__name AS theatre, " +
                           "MAX(similarity) AS similarity " +
                    "ORDER BY similarity DESC";
                
                Map<String, Object> params = new HashMap<>();
                params.put("pastSessionIds", pastSessionIds);
                params.put("minScore", minScore);
                
                Result recommendationsResult = tx.execute(recommendationsQuery, params);
                
                while (recommendationsResult.hasNext()) {
                    Map<String, Object> row = recommendationsResult.next();
                    recommendations.add(new SessionRecommendation(
                        (String) row.get("sessionId"),
                        (String) row.get("title"),
                        (String) row.get("stream"),
                        (String) row.get("synopsis"),
                        (String) row.get("date"),
                        (String) row.get("startTime"),
                        (String) row.get("endTime"),
                        (String) row.get("theatre"),
                        (Double) row.get("similarity")
                    ));
                }
            }
            
            // Apply maxRecommendations limit if specified
            if (maxRecommendations != null && maxRecommendations > 0 && recommendations.size() > maxRecommendations) {
                recommendations = recommendations.subList(0, maxRecommendations.intValue());
            }
            
            tx.commit();
        } catch (Exception e) {
            log.error("Error recommending sessions: " + e.getMessage(), e);
        }
        
        return recommendations.stream();
    }
    
    /**
     * Result class for session recommendations.
     */
    public static class SessionRecommendation {
        public String sessionId;
        public String title;
        public String stream;
        public String synopsis;
        public String date;
        public String startTime;
        public String endTime;
        public String theatre;
        public Double similarityScore;
        
        public SessionRecommendation(
                String sessionId, String title, String stream, String synopsis,
                String date, String startTime, String endTime, String theatre,
                Double similarityScore) {
            this.sessionId = sessionId;
            this.title = title;
            this.stream = stream;
            this.synopsis = synopsis;
            this.date = date;
            this.startTime = startTime;
            this.endTime = endTime;
            this.theatre = theatre;
            this.similarityScore = similarityScore;
        }
    }
}