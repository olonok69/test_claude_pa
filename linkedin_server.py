"""
LinkedIn MCP Server

A Model Context Protocol server that provides LinkedIn API functionality
using the open_linkedin_api library.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from open_linkedin_api import Linkedin
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # Send logs to stderr so they appear in Claude Desktop logs
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("LinkedIn API Server")

# Global LinkedIn client
linkedin_client: Optional[Linkedin] = None


class ProfileContact(BaseModel):
    """Contact information for a LinkedIn profile"""
    email_address: Optional[str] = None
    websites: List[Dict[str, Any]] = Field(default_factory=list)
    twitter: Optional[List[str]] = None
    phone_numbers: List[Dict[str, Any]] = Field(default_factory=list)


class ConnectionInfo(BaseModel):
    """Information about a LinkedIn connection"""
    urn_id: str
    distance: Optional[str] = None
    jobtitle: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


class SearchResult(BaseModel):
    """LinkedIn search result"""
    results: List[Dict[str, Any]]
    total_results: int


class MessageResult(BaseModel):
    """Result of sending a LinkedIn message"""
    success: bool
    error_message: Optional[str] = None


def get_linkedin_client() -> Linkedin:
    """Get or create LinkedIn client"""
    global linkedin_client
    
    if linkedin_client is None:
        username = os.getenv("LINKEDIN_USERNAME")
        password = os.getenv("LINKEDIN_PASSWORD")
        
        if not username or not password:
            logger.error("LinkedIn credentials not found in environment variables")
            raise ValueError("LinkedIn credentials not found in environment variables")
        
        try:
            logger.info(f"Initializing LinkedIn client for user: {username}")
            linkedin_client = Linkedin(username, password)
            logger.info("LinkedIn client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn client: {e}")
            raise
    
    return linkedin_client


@mcp.tool()
def get_profile(public_id: Optional[str] = None, urn_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get LinkedIn profile information by public ID or URN ID.
    
    Args:
        public_id: LinkedIn public identifier (e.g., 'john-doe-123')
        urn_id: LinkedIn URN identifier
    
    Returns:
        Profile data including name, experience, education, skills, etc.
    """
    try:
        logger.info(f"Getting profile: public_id={public_id}, urn_id={urn_id}")
        client = get_linkedin_client()
        
        if not public_id and not urn_id:
            raise ValueError("Either public_id or urn_id must be provided")
        
        profile = client.get_profile(public_id=public_id, urn_id=urn_id)
        logger.info("Profile retrieved successfully")
        return profile
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_profile_contact_info(public_id: Optional[str] = None, urn_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get contact information for a LinkedIn profile.
    
    Args:
        public_id: LinkedIn public identifier
        urn_id: LinkedIn URN identifier
    
    Returns:
        Contact information including email, websites, phone numbers
    """
    try:
        logger.info(f"Getting contact info: public_id={public_id}, urn_id={urn_id}")
        client = get_linkedin_client()
        
        if not public_id and not urn_id:
            raise ValueError("Either public_id or urn_id must be provided")
        
        contact_info = client.get_profile_contact_info(public_id=public_id, urn_id=urn_id)
        logger.info("Contact info retrieved successfully")
        return contact_info
    except Exception as e:
        logger.error(f"Error getting contact info: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_profile_connections(urn_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get connections for a LinkedIn profile.
    
    Args:
        urn_id: LinkedIn URN identifier
        limit: Maximum number of connections to return
    
    Returns:
        List of connection information
    """
    try:
        logger.info(f"Getting connections: urn_id={urn_id}, limit={limit}")
        client = get_linkedin_client()
        connections = client.get_profile_connections(urn_id, limit=limit)
        
        result = []
        for conn in connections:
            result.append({
                "urn_id": conn.get("urn_id", ""),
                "distance": conn.get("distance"),
                "jobtitle": conn.get("jobtitle"),
                "location": conn.get("location"),
                "name": conn.get("name")
            })
        
        logger.info(f"Retrieved {len(result)} connections")
        return result
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return []


@mcp.tool()
def search_people(
    keywords: Optional[str] = None,
    current_company: Optional[List[str]] = None,
    past_companies: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    industries: Optional[List[str]] = None,
    schools: Optional[List[str]] = None,
    network_depths: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for people on LinkedIn.
    
    Args:
        keywords: Search keywords
        current_company: List of current company URN IDs
        past_companies: List of past company URN IDs
        regions: List of region URN IDs
        industries: List of industry URN IDs
        schools: List of school URN IDs
        network_depths: Connection levels ("F", "S", "O" for 1st, 2nd, 3rd+)
        limit: Maximum number of results
    
    Returns:
        Search results with people data
    """
    try:
        logger.info(f"Searching people: keywords={keywords}, limit={limit}")
        client = get_linkedin_client()
        
        # Ensure limit is reasonable
        limit = min(limit, 49)  # LinkedIn API limit
        
        results = client.search_people(
            keywords=keywords,
            current_company=current_company,
            past_companies=past_companies,
            regions=regions,
            industries=industries,
            schools=schools,
            network_depths=network_depths,
            limit=limit
        )
        
        logger.info(f"Search completed successfully, found {len(results)} results")
        return {
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching people: {e}")
        return {
            "results": [],
            "total_results": 0,
            "error": str(e)
        }


@mcp.tool()
def search_companies(keywords: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Search for companies on LinkedIn.
    
    Args:
        keywords: Search keywords
        limit: Maximum number of results
    
    Returns:
        Search results with company data
    """
    try:
        logger.info(f"Searching companies: keywords={keywords}, limit={limit}")
        client = get_linkedin_client()
        
        # Ensure limit is reasonable
        limit = min(limit, 49)  # LinkedIn API limit
        
        results = client.search_companies(keywords=keywords, limit=limit)
        
        logger.info(f"Company search completed successfully, found {len(results)} results")
        return {
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        return {
            "results": [],
            "total_results": 0,
            "error": str(e)
        }


@mcp.tool()
def get_company(public_id: str) -> Dict[str, Any]:
    """
    Get LinkedIn company information.
    
    Args:
        public_id: Company public identifier
    
    Returns:
        Company data including name, description, industry, etc.
    """
    try:
        logger.info(f"Getting company: public_id={public_id}")
        client = get_linkedin_client()
        company = client.get_company(public_id)
        logger.info("Company data retrieved successfully")
        return company
    except Exception as e:
        logger.error(f"Error getting company: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_profile_posts(
    public_id: Optional[str] = None,
    urn_id: Optional[str] = None,
    post_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Get posts from a LinkedIn profile.
    
    Args:
        public_id: LinkedIn public identifier
        urn_id: LinkedIn URN identifier
        post_count: Number of posts to retrieve
    
    Returns:
        List of posts from the profile
    """
    try:
        logger.info(f"Getting profile posts: public_id={public_id}, urn_id={urn_id}, count={post_count}")
        client = get_linkedin_client()
        
        posts = client.get_profile_posts(
            public_id=public_id,
            urn_id=urn_id,
            post_count=post_count
        )
        
        logger.info(f"Retrieved {len(posts)} posts")
        return posts
    except Exception as e:
        logger.error(f"Error getting profile posts: {e}")
        return []


@mcp.tool()
def send_message(
    message_body: str,
    conversation_urn_id: Optional[str] = None,
    recipients: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send a message on LinkedIn.
    
    Args:
        message_body: The message text to send
        conversation_urn_id: Existing conversation URN ID
        recipients: List of recipient profile URN IDs (for new conversations)
    
    Returns:
        Result indicating success or failure
    """
    try:
        logger.info(f"Sending message: body_length={len(message_body)}")
        client = get_linkedin_client()
        
        error = client.send_message(
            message_body=message_body,
            conversation_urn_id=conversation_urn_id,
            recipients=recipients
        )
        
        success = not error
        logger.info(f"Message send result: success={success}")
        return {
            "success": success,
            "error_message": str(error) if error else None
        }
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"success": False, "error_message": str(e)}


@mcp.tool()
def get_conversations() -> List[Dict[str, Any]]:
    """
    Get list of LinkedIn conversations.
    
    Returns:
        List of conversation data
    """
    try:
        logger.info("Getting conversations")
        client = get_linkedin_client()
        conversations = client.get_conversations()
        result = conversations.get("elements", [])
        logger.info(f"Retrieved {len(result)} conversations")
        return result
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return []


@mcp.tool()
def get_conversation_details(profile_urn_id: str) -> Dict[str, Any]:
    """
    Get conversation details for a specific profile.
    
    Args:
        profile_urn_id: Profile URN ID to get conversation with
    
    Returns:
        Conversation details
    """
    try:
        logger.info(f"Getting conversation details: profile_urn_id={profile_urn_id}")
        client = get_linkedin_client()
        details = client.get_conversation_details(profile_urn_id)
        logger.info("Conversation details retrieved successfully")
        return details
    except Exception as e:
        logger.error(f"Error getting conversation details: {e}")
        return {"error": str(e)}


@mcp.tool()
def add_connection(
    profile_public_id: str,
    message: str = "",
    profile_urn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a connection request to a LinkedIn profile.
    
    Args:
        profile_public_id: Public ID of the profile to connect with
        message: Optional message to include with connection request (max 300 chars)
        profile_urn: Optional profile URN
    
    Returns:
        Result indicating success or failure
    """
    try:
        logger.info(f"Adding connection: profile_public_id={profile_public_id}")
        client = get_linkedin_client()
        
        error = client.add_connection(
            profile_public_id=profile_public_id,
            message=message,
            profile_urn=profile_urn
        )
        
        success = not error
        logger.info(f"Connection request result: success={success}")
        return {
            "success": success,
            "error": str(error) if error else None,
            "message": "Connection request sent successfully" if success else "Failed to send connection request"
        }
    except Exception as e:
        logger.error(f"Error adding connection: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_current_user_profile() -> Dict[str, Any]:
    """
    Get the current authenticated user's profile.
    
    Returns:
        Current user's profile data
    """
    try:
        logger.info("Getting current user profile")
        client = get_linkedin_client()
        profile = client.get_user_profile()
        logger.info("Current user profile retrieved successfully")
        return profile
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        return {"error": str(e)}


@mcp.resource("linkedin://profile/{public_id}")
def get_profile_resource(public_id: str) -> str:
    """Get LinkedIn profile as a resource"""
    try:
        logger.info(f"Getting profile resource: public_id={public_id}")
        client = get_linkedin_client()
        profile = client.get_profile(public_id=public_id)
        
        # Format profile data as readable text
        output = f"LinkedIn Profile: {profile.get('firstName', '')} {profile.get('lastName', '')}\n"
        output += f"Headline: {profile.get('headline', 'N/A')}\n"
        output += f"Location: {profile.get('geoLocationName', 'N/A')}\n"
        output += f"Industry: {profile.get('industryName', 'N/A')}\n"
        output += f"Summary: {profile.get('summary', 'N/A')}\n\n"
        
        if profile.get('experience'):
            output += "Experience:\n"
            for exp in profile['experience'][:3]:  # Show top 3 experiences
                output += f"- {exp.get('title', 'N/A')} at {exp.get('companyName', 'N/A')}\n"
        
        logger.info("Profile resource formatted successfully")
        return output
    except Exception as e:
        logger.error(f"Error retrieving profile resource: {e}")
        return f"Error retrieving profile: {str(e)}"


@mcp.resource("linkedin://company/{public_id}")
def get_company_resource(public_id: str) -> str:
    """Get LinkedIn company as a resource"""
    try:
        logger.info(f"Getting company resource: public_id={public_id}")
        client = get_linkedin_client()
        company = client.get_company(public_id)
        
        # Format company data as readable text
        output = f"Company: {company.get('name', 'N/A')}\n"
        output += f"Industry: {company.get('companyIndustries', [{}])[0].get('localizedName', 'N/A')}\n"
        output += f"Headquarters: {company.get('headquarter', {}).get('city', 'N/A')}\n"
        output += f"Company Size: {company.get('staffCountRange', {}).get('start', 'N/A')}-{company.get('staffCountRange', {}).get('end', 'N/A')} employees\n"
        output += f"Description: {company.get('description', 'N/A')}\n"
        
        logger.info("Company resource formatted successfully")
        return output
    except Exception as e:
        logger.error(f"Error retrieving company resource: {e}")
        return f"Error retrieving company: {str(e)}"


if __name__ == "__main__":
    try:
        logger.info("Starting LinkedIn MCP Server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)