# PA Application Features

Based on the `PA/config/config_tsl.yaml` configuration file, here is a list of key features offered by the PA (Personal Agendas) application:

- **Multi-Mode Operation**: Supports "personal_agendas" and "engagement" modes for different campaign types.
- **Event Configuration**: Configurable event details (names, years, shows) for primary and secondary events.
- **Data Processing Pipeline**: Processes registration data, scan data, and session data with configurable input/output files.
- **Neo4j Knowledge Graph Integration**: Creates nodes (visitors, sessions, streams, shows) and relationships (attended sessions, same visitor, job/stream mappings).
- **Session Embeddings**: Generates ML embeddings for sessions using models like all-MiniLM-L6-v2.
- **Personalized Recommendations**: Provides session recommendations based on similarity scores, with configurable thresholds and limits.
- **Control Group Management**: Supports control groups with percentage-based sampling and random seeding for testing.
- **Parallel Processing**: Enables multi-worker parallel processing for recommendations.
- **Similarity Matching**: Calculates visitor similarity using weighted attributes (sector, country, seniority, etc.).
- **Session Filtering**: Removes invalid sessions based on titles, keywords, and regex patterns.
- **Theatre Capacity Limits**: Optional capacity-based filtering for session recommendations.
- **External Recommendations Integration**: Supports importing external recommendation files.
- **LangChain Filtering**: Optional AI-powered filtering for recommendations.
- **Job and Specialization Mappings**: Maps job roles and specializations to streams in Neo4j.
- **Output Formats**: Exports recommendations in CSV and JSON formats, with minimal CSV options.
- **Engagement Mode Features**: Mailing suppression, returning visitor flags, and historical data handling.
- **Post-Analysis Mode**: Processes additional scan and entry data for analysis.
- **Practice Matching**: Matches companies and practice types with configurable thresholds.
- **Demographic Analysis**: Processes and combines registration and demographic data.
- **Logging and Monitoring**: Configurable logging levels and file outputs.
- **Language Model Integration**: Uses GPT models for advanced processing (e.g., filtering).
- **Badge and Visitor Validation**: Validates badge types and handles visitor properties.
- **Stream Processing**: Creates and manages stream catalogs with enhanced descriptions.

## Filtering Capabilities

The PA application includes comprehensive filtering capabilities to refine session recommendations and ensure relevance and compliance:

- **Practice Type Filtering**: Filters sessions based on visitor's practice type (e.g., veterinary specializations) using configurable field mappings and rules.
- **Role-Based Filtering**: Applies specific filtering rules based on job roles (e.g., limiting nurse roles to relevant streams).
- **Engagement Show-Theatre Filter**: Restricts engagement mode recommendations to theatres mapped from the visitor's last-year show attendance, with configurable mapping files and strictness options.
- **Theatre Capacity Limits**: Enforces per-theatre capacity constraints by trimming recommendations when slots exceed configured limits, with adjustable multipliers.
- **Session Title Filtering**: Removes invalid sessions based on title patterns, keywords, and regex expressions (e.g., "TBC", "to be confirmed", sponsored sessions).
- **LangChain AI Filtering**: Optional advanced filtering using LangChain and GPT models for intelligent recommendation refinement.
- **Overlapping Session Resolution**: Resolves scheduling conflicts by keeping sessions with highest similarity scores when overlaps occur.
- **Day Balancing**: Optionally balances recommendations across multiple days to ensure even distribution, with strict or flexible enforcement.
- **Minimal CSV Export Filtering**: Filters exported CSV fields to include only essential data (session_id, visitor_id, email, etc.).
- **Similarity Score Thresholding**: Filters recommendations below configurable minimum similarity scores.
- **Maximum Recommendations Limit**: Caps the number of recommendations per visitor with configurable limits.
- **Control Group Filtering**: Applies percentage-based filtering for A/B testing scenarios with random seeding.
- **External Recommendations Filtering**: Integrates and filters external recommendation sources (e.g., exhibitor recommendations).
- **Returning Visitor Adjustments**: Applies similarity score adjustments for returning visitors without historical attendance data.
- **Badge Type Validation**: Filters visitors based on valid badge types to ensure appropriate audience targeting.
- **Show-Specific Filtering**: Applies different filtering rules based on event/show configuration for multi-event support.