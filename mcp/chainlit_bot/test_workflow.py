#!/usr/bin/env python3
"""
Test script demonstrating flexible query approach for job titles
"""
import asyncio
from mcp_client import MCPClient

async def test_flexible_job_search():
    """Demonstrate flexible job title searching"""
    print("🔍 Testing Flexible Job Title Search\n")
    
    client = MCPClient()
    
    try:
        await client.connect_from_config()
        
        if not client.is_connected():
            print("❌ Failed to connect")
            return
        
        print("✅ Connected to Neo4j")
        
        # Step 1: Get schema
        print("\n" + "="*50)
        print("📋 STEP 1: Getting Schema")
        print("="*50)
        
        schema_result = await client.call_tool("neo4j-aura", "get_neo4j_schema", {})
        print("Schema obtained ✅")
        
        # Step 2: Explore job titles that might relate to "surgeon"
        print("\n" + "="*50)
        print("🔍 STEP 2: Exploring Job Titles (Flexible Search)")
        print("="*50)
        
        exploration_queries = [
            # Find all distinct job titles to see what's available
            "MATCH (n) WHERE any(prop in keys(n) WHERE prop IN ['jobTitle', 'job_title', 'title', 'role']) RETURN DISTINCT keys(n) as properties LIMIT 10",
            
            # Try different property names for job titles
            "MATCH (n) WHERE n.jobTitle IS NOT NULL RETURN DISTINCT n.jobTitle as JobTitles ORDER BY JobTitles LIMIT 20",
            
            # If jobTitle doesn't work, try other common property names
            "MATCH (n) WHERE n.job_title IS NOT NULL RETURN DISTINCT n.job_title as JobTitles ORDER BY JobTitles LIMIT 20",
            "MATCH (n) WHERE n.title IS NOT NULL RETURN DISTINCT n.title as JobTitles ORDER BY JobTitles LIMIT 20",
            "MATCH (n) WHERE n.role IS NOT NULL RETURN DISTINCT n.role as JobTitles ORDER BY JobTitles LIMIT 20",
        ]
        
        job_property = None
        available_jobs = []
        
        for query in exploration_queries:
            try:
                print(f"\n🔍 Exploring: {query}")
                result = await client.call_tool("neo4j-aura", "read_neo4j_cypher", {"query": query})
                
                for item in result.content:
                    if item.text and "JobTitles" in item.text:
                        print(f"✅ Found job titles: {item.text}")
                        available_jobs.extend(item.text.split())
                        if "jobTitle" in query:
                            job_property = "jobTitle"
                        elif "job_title" in query:
                            job_property = "job_title"
                        elif "title" in query:
                            job_property = "title"
                        elif "role" in query:
                            job_property = "role"
                        break
                
                if available_jobs:
                    break
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Step 3: Search for surgeon-related titles
        if job_property and available_jobs:
            print(f"\n" + "="*50)
            print(f"🎯 STEP 3: Finding Surgeon-Related Jobs (using {job_property})")
            print("="*50)
            
            surgeon_search_query = f"""
            MATCH (n) 
            WHERE n.{job_property} IS NOT NULL 
            AND (toLower(n.{job_property}) CONTAINS 'surgeon' 
                 OR toLower(n.{job_property}) CONTAINS 'surg' 
                 OR toLower(n.{job_property}) CONTAINS 'medical'
                 OR toLower(n.{job_property}) CONTAINS 'doctor'
                 OR toLower(n.{job_property}) CONTAINS 'vet')
            RETURN DISTINCT n.{job_property} as SurgeonJobs, count(n) as Count
            ORDER BY Count DESC
            """
            
            try:
                print(f"🔍 Surgeon search query: {surgeon_search_query}")
                result = await client.call_tool("neo4j-aura", "read_neo4j_cypher", {"query": surgeon_search_query})
                
                surgeon_jobs = []
                for item in result.content:
                    print(f"✅ Surgeon-related jobs found: {item.text}")
                    surgeon_jobs.append(item.text)
                
                # Step 4: Build final query using found surgeon jobs
                if surgeon_jobs:
                    print(f"\n" + "="*50)
                    print("🚀 STEP 4: Final Query with Found Jobs")
                    print("="*50)
                    
                    # This would be the actual query for sessions recommended to surgeons
                    final_query = f"""
                    MATCH (v)-[r]->(s)
                    WHERE v.{job_property} IS NOT NULL 
                    AND (toLower(v.{job_property}) CONTAINS 'surgeon' 
                         OR toLower(v.{job_property}) CONTAINS 'surg')
                    RETURN type(r) as relationship, labels(v) as visitorType, labels(s) as sessionType, count(*) as count
                    ORDER BY count DESC
                    LIMIT 5
                    """
                    
                    print(f"🔍 Final query: {final_query}")
                    result = await client.call_tool("neo4j-aura", "read_neo4j_cypher", {"query": final_query})
                    
                    for item in result.content:
                        print(f"✅ Final results: {item.text}")
                        
            except Exception as e:
                print(f"❌ Surgeon search failed: {e}")
        
        print(f"\n🎉 Flexible search demo completed!")
        print("\n💡 This demonstrates how the chatbot should:")
        print("1. ✅ Explore different property names for job titles")
        print("2. ✅ Use flexible matching (CONTAINS, case-insensitive)")
        print("3. ✅ Find variations like 'Vet Surgeon', 'Heart Surgeon'")
        print("4. ✅ Build inclusive final queries")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.close_all()

if __name__ == "__main__":
    asyncio.run(test_flexible_job_search())