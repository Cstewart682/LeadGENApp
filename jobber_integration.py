#!/usr/bin/env python3
"""
Jobber CRM Integration

Integrates with Jobber's GraphQL API to sync leads as clients.

Jobber API Documentation: https://developer.getjobber.com/docs/
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JobberConfig:
    """Jobber API configuration."""
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:5000/oauth/callback"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None


class JobberAPI:
    """
    Jobber GraphQL API client.
    
    Setup:
    1. Create a developer account at https://developer.getjobber.com/
    2. Create an app in the Developer Center
    3. Get your Client ID and Client Secret
    4. Set up OAuth redirect URI
    
    Usage:
        jobber = JobberAPI(client_id="...", client_secret="...")
        
        # First time: Get authorization URL and complete OAuth flow
        auth_url = jobber.get_authorization_url()
        # User visits auth_url, authorizes, gets redirected with code
        jobber.exchange_code_for_token(code)
        
        # Create client from lead
        jobber.create_client(lead)
    """
    
    API_URL = "https://api.getjobber.com/api/graphql"
    AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
    TOKEN_URL = "https://api.getjobber.com/api/oauth/token"
    API_VERSION = "2023-11-15"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:5000/oauth/callback",
        access_token: str = None,
        refresh_token: str = None
    ):
        self.config = JobberConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            access_token=access_token,
            refresh_token=refresh_token
        )
        self.session = requests.Session()
    
    # =========================================================================
    # OAuth Flow
    # =========================================================================
    
    def get_authorization_url(self, scopes: list[str] = None) -> str:
        """
        Get the OAuth authorization URL.
        
        User should visit this URL to authorize the app.
        """
        if scopes is None:
            scopes = ["read_clients", "write_clients", "read_jobs", "write_jobs"]
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes)
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    def exchange_code_for_token(self, code: str) -> bool:
        """
        Exchange authorization code for access token.
        
        Call this after user authorizes and is redirected with a code.
        """
        response = self.session.post(
            self.TOKEN_URL,
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.config.access_token = data.get("access_token")
            self.config.refresh_token = data.get("refresh_token")
            logger.info("Successfully obtained Jobber access token")
            return True
        else:
            logger.error(f"Failed to exchange code: {response.text}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.config.refresh_token:
            logger.error("No refresh token available")
            return False
        
        response = self.session.post(
            self.TOKEN_URL,
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.config.refresh_token
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.config.access_token = data.get("access_token")
            self.config.refresh_token = data.get("refresh_token", self.config.refresh_token)
            logger.info("Successfully refreshed Jobber access token")
            return True
        else:
            logger.error(f"Failed to refresh token: {response.text}")
            return False
    
    def save_tokens(self, filepath: str = "jobber_tokens.json"):
        """Save tokens to file for persistence."""
        with open(filepath, 'w') as f:
            json.dump({
                "access_token": self.config.access_token,
                "refresh_token": self.config.refresh_token
            }, f)
    
    def load_tokens(self, filepath: str = "jobber_tokens.json") -> bool:
        """Load tokens from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.config.access_token = data.get("access_token")
                self.config.refresh_token = data.get("refresh_token")
                return True
        except FileNotFoundError:
            return False
    
    # =========================================================================
    # GraphQL Queries
    # =========================================================================
    
    def _execute_query(self, query: str, variables: dict = None) -> dict:
        """Execute a GraphQL query."""
        if not self.config.access_token:
            raise Exception("No access token. Complete OAuth flow first.")
        
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
            "X-JOBBER-GRAPHQL-VERSION": self.API_VERSION
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = self.session.post(
            self.API_URL,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 401:
            # Token expired, try to refresh
            if self.refresh_access_token():
                headers["Authorization"] = f"Bearer {self.config.access_token}"
                response = self.session.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
        
        if response.status_code != 200:
            logger.error(f"GraphQL request failed: {response.text}")
            return {"errors": [{"message": response.text}]}
        
        return response.json()
    
    # =========================================================================
    # Client Operations
    # =========================================================================
    
    def create_client(self, lead: dict) -> Optional[str]:
        """
        Create a new client in Jobber from a lead.
        
        Args:
            lead: Dictionary with lead data:
                - company_name: str
                - contact_name: str (optional)
                - general_email: str (optional)
                - general_phone: str (optional)
                - address: str (optional)
                - city: str (optional)
                - province: str (optional)
                - notes: str (optional)
        
        Returns:
            Jobber client ID if successful, None otherwise
        """
        # Determine if this is a company or individual
        is_company = bool(lead.get('company_name'))
        
        # Build the input
        client_input = {
            "isCompany": is_company,
        }
        
        if is_company:
            client_input["companyName"] = lead.get('company_name', '')
        
        # Contact name parsing
        contact_name = lead.get('contact_name', '')
        if contact_name:
            parts = contact_name.split(' ', 1)
            client_input["firstName"] = parts[0]
            client_input["lastName"] = parts[1] if len(parts) > 1 else ""
        elif not is_company:
            client_input["firstName"] = lead.get('company_name', 'Unknown')
            client_input["lastName"] = ""
        
        # Email
        emails = []
        if lead.get('general_email'):
            emails.append({
                "description": "Main",
                "address": lead['general_email'],
                "primary": True
            })
        if lead.get('contact_email'):
            emails.append({
                "description": "Direct",
                "address": lead['contact_email'],
                "primary": not bool(lead.get('general_email'))
            })
        if emails:
            client_input["emails"] = emails
        
        # Phone
        phones = []
        if lead.get('general_phone'):
            phones.append({
                "description": "Main",
                "number": lead['general_phone'],
                "primary": True
            })
        if lead.get('contact_phone'):
            phones.append({
                "description": "Direct",
                "number": lead['contact_phone'],
                "primary": not bool(lead.get('general_phone'))
            })
        if phones:
            client_input["phones"] = phones
        
        # Address (as billing address)
        if lead.get('address') or lead.get('city'):
            client_input["billingAddress"] = {
                "street1": lead.get('address', ''),
                "city": lead.get('city', ''),
                "province": lead.get('province', 'AB'),
                "country": "Canada"
            }
        
        query = """
        mutation CreateClient($input: ClientCreateInput!) {
            clientCreate(input: $input) {
                client {
                    id
                    name
                    jobberWebUri
                }
                userErrors {
                    message
                    path
                }
            }
        }
        """
        
        result = self._execute_query(query, {"input": client_input})
        
        if result.get('errors'):
            logger.error(f"GraphQL errors: {result['errors']}")
            return None
        
        data = result.get('data', {}).get('clientCreate', {})
        
        if data.get('userErrors'):
            logger.error(f"User errors: {data['userErrors']}")
            return None
        
        client = data.get('client', {})
        client_id = client.get('id')
        
        if client_id:
            logger.info(f"Created Jobber client: {client.get('name')} (ID: {client_id})")
            
            # Add note if there's additional info
            if lead.get('notes') or lead.get('industry') or lead.get('source'):
                note_parts = []
                if lead.get('industry'):
                    note_parts.append(f"Industry: {lead['industry']}")
                if lead.get('source'):
                    note_parts.append(f"Source: {lead['source']}")
                if lead.get('contact_title'):
                    note_parts.append(f"Contact Title: {lead['contact_title']}")
                if lead.get('notes'):
                    note_parts.append(f"Notes: {lead['notes']}")
                
                if note_parts:
                    self.add_client_note(client_id, "\n".join(note_parts))
        
        return client_id
    
    def add_client_note(self, client_id: str, note: str) -> bool:
        """Add a note to a client."""
        query = """
        mutation AddClientNote($clientId: EncodedId!, $note: String!) {
            clientNoteCreate(clientId: $clientId, note: $note) {
                clientNote {
                    id
                }
                userErrors {
                    message
                }
            }
        }
        """
        
        result = self._execute_query(query, {
            "clientId": client_id,
            "note": note
        })
        
        return not bool(result.get('errors'))
    
    def get_clients(self, limit: int = 50) -> list[dict]:
        """Get list of existing clients."""
        query = """
        query GetClients($first: Int!) {
            clients(first: $first) {
                nodes {
                    id
                    name
                    companyName
                    emails {
                        address
                    }
                    phones {
                        number
                    }
                    isLead
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        result = self._execute_query(query, {"first": limit})
        
        if result.get('errors'):
            return []
        
        return result.get('data', {}).get('clients', {}).get('nodes', [])
    
    def search_client_by_email(self, email: str) -> Optional[dict]:
        """Search for a client by email to avoid duplicates."""
        clients = self.get_clients(limit=100)
        
        for client in clients:
            for client_email in client.get('emails', []):
                if client_email.get('address', '').lower() == email.lower():
                    return client
        
        return None
    
    def create_or_update_client(self, lead: dict) -> tuple[str, bool]:
        """
        Create a client or return existing one if email matches.
        
        Returns:
            Tuple of (client_id, was_created)
        """
        # Check if client already exists
        if lead.get('general_email'):
            existing = self.search_client_by_email(lead['general_email'])
            if existing:
                logger.info(f"Client already exists: {existing.get('name')} (ID: {existing.get('id')})")
                return existing.get('id'), False
        
        # Create new client
        client_id = self.create_client(lead)
        return client_id, True
    
    # =========================================================================
    # Batch Operations
    # =========================================================================
    
    def sync_leads_to_jobber(self, leads: list[dict], skip_existing: bool = True) -> dict:
        """
        Sync multiple leads to Jobber as clients.
        
        Args:
            leads: List of lead dictionaries
            skip_existing: If True, skip leads with emails that already exist
        
        Returns:
            Summary of sync results
        """
        results = {
            "created": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }
        
        for lead in leads:
            try:
                if skip_existing and lead.get('general_email'):
                    existing = self.search_client_by_email(lead['general_email'])
                    if existing:
                        results["skipped"] += 1
                        results["details"].append({
                            "company": lead.get('company_name'),
                            "status": "skipped",
                            "reason": "Already exists in Jobber"
                        })
                        continue
                
                client_id = self.create_client(lead)
                
                if client_id:
                    results["created"] += 1
                    results["details"].append({
                        "company": lead.get('company_name'),
                        "status": "created",
                        "jobber_id": client_id
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "company": lead.get('company_name'),
                        "status": "failed",
                        "reason": "API error"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "company": lead.get('company_name'),
                    "status": "failed",
                    "reason": str(e)
                })
        
        logger.info(f"Sync complete: {results['created']} created, {results['skipped']} skipped, {results['failed']} failed")
        return results


# =============================================================================
# CLI Usage
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Jobber CRM Integration")
    print("=" * 60)
    print("""
Setup Instructions:
-------------------

1. Create a Jobber Developer Account:
   https://developer.getjobber.com/

2. Create an App in the Developer Center:
   - Go to Developer Center > Manage Apps > New
   - Set Redirect URI to: http://localhost:5000/oauth/callback
   - Note your Client ID and Client Secret

3. Configure the integration:
   
   from jobber_integration import JobberAPI
   
   jobber = JobberAPI(
       client_id="your_client_id",
       client_secret="your_client_secret"
   )

4. Complete OAuth Flow (first time only):
   
   # Get the authorization URL
   auth_url = jobber.get_authorization_url()
   print(f"Visit: {auth_url}")
   
   # After authorizing, you'll be redirected with a code
   # Exchange it for tokens:
   jobber.exchange_code_for_token("the_code_from_redirect")
   
   # Save tokens for later
   jobber.save_tokens()

5. Sync leads to Jobber:
   
   # Load saved tokens
   jobber.load_tokens()
   
   # Create a single client
   lead = {
       "company_name": "ABC Manufacturing",
       "contact_name": "John Smith",
       "general_email": "info@abcmfg.ca",
       "general_phone": "(403) 555-1234",
       "industry": "Manufacturing",
       "source": "Lead Generator"
   }
   
   client_id = jobber.create_client(lead)
   
   # Or sync multiple leads
   results = jobber.sync_leads_to_jobber(leads_list)
    """)
