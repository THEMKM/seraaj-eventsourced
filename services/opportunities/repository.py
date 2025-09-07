"""
Opportunities repository implementing file-based storage
"""
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from .models import Opportunity, OpportunityStatus


class OpportunityRepository:
    """File-based repository for opportunities"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.opportunities_file = self.data_dir / "opportunities.json"
        self._cache: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load opportunities from disk"""
        if self.opportunities_file.exists():
            try:
                with open(self.opportunities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = data
                    elif isinstance(data, list):
                        # Convert list to dict for compatibility
                        self._cache = {opp.get("id", str(uuid4())): opp for opp in data}
            except Exception as e:
                print(f"Error loading opportunities: {e}")
                self._cache = {}
    
    def _save(self):
        """Save opportunities to disk"""
        try:
            temp_file = self.opportunities_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, default=str, ensure_ascii=False)
            temp_file.replace(self.opportunities_file)
        except Exception as e:
            print(f"Error saving opportunities: {e}")
            raise
    
    async def create(self, opportunity: Opportunity) -> Opportunity:
        """Create a new opportunity"""
        opportunity.id = str(uuid4())
        opportunity.created_at = datetime.now(timezone.utc)
        opportunity.updated_at = opportunity.created_at
        
        # Convert to dict for storage
        opp_dict = opportunity.model_dump()
        opp_dict['created_at'] = opportunity.created_at.isoformat()
        opp_dict['updated_at'] = opportunity.updated_at.isoformat()
        if opportunity.start_date:
            opp_dict['start_date'] = opportunity.start_date.isoformat()
        if opportunity.end_date:
            opp_dict['end_date'] = opportunity.end_date.isoformat()
        if opportunity.application_deadline:
            opp_dict['application_deadline'] = opportunity.application_deadline.isoformat()
        
        self._cache[opportunity.id] = opp_dict
        self._save()
        
        return opportunity
    
    async def get(self, opportunity_id: str) -> Optional[Opportunity]:
        """Get opportunity by ID"""
        opp_data = self._cache.get(opportunity_id)
        if not opp_data:
            return None
        
        return self._dict_to_opportunity(opp_data)
    
    async def update(self, opportunity_id: str, updates: Dict) -> Optional[Opportunity]:
        """Update an existing opportunity"""
        if opportunity_id not in self._cache:
            return None
        
        opp_data = self._cache[opportunity_id].copy()
        
        # Apply updates
        for field, value in updates.items():
            if value is not None:
                if isinstance(value, datetime):
                    opp_data[field] = value.isoformat()
                else:
                    opp_data[field] = value
        
        opp_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        self._cache[opportunity_id] = opp_data
        self._save()
        
        return self._dict_to_opportunity(opp_data)
    
    async def delete(self, opportunity_id: str) -> bool:
        """Delete an opportunity"""
        if opportunity_id in self._cache:
            del self._cache[opportunity_id]
            self._save()
            return True
        return False
    
    async def list_opportunities(
        self,
        limit: int = 20,
        offset: int = 0,
        organization_id: Optional[str] = None,
        status: Optional[OpportunityStatus] = None,
        category: Optional[str] = None
    ) -> List[Opportunity]:
        """List opportunities with filtering"""
        opportunities = []
        
        for opp_data in self._cache.values():
            # Apply filters
            if organization_id and opp_data.get('organization_id') != organization_id:
                continue
            if status and opp_data.get('status') != status.value:
                continue
            if category and opp_data.get('category') != category:
                continue
            
            try:
                opportunity = self._dict_to_opportunity(opp_data)
                opportunities.append(opportunity)
            except Exception as e:
                print(f"Error parsing opportunity {opp_data.get('id')}: {e}")
                continue
        
        # Sort by creation date (newest first)
        opportunities.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return opportunities[offset:offset + limit]
    
    async def get_by_organization(self, organization_id: str) -> List[Opportunity]:
        """Get all opportunities for an organization"""
        return await self.list_opportunities(organization_id=organization_id, limit=1000)
    
    async def count_total(self, organization_id: Optional[str] = None) -> int:
        """Count total opportunities"""
        if organization_id:
            return len([
                opp for opp in self._cache.values()
                if opp.get('organization_id') == organization_id
            ])
        return len(self._cache)
    
    def _dict_to_opportunity(self, opp_data: Dict) -> Opportunity:
        """Convert dictionary to Opportunity model"""
        # Parse datetime fields
        parsed_data = opp_data.copy()
        
        if 'created_at' in parsed_data and isinstance(parsed_data['created_at'], str):
            parsed_data['created_at'] = datetime.fromisoformat(parsed_data['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in parsed_data and isinstance(parsed_data['updated_at'], str):
            parsed_data['updated_at'] = datetime.fromisoformat(parsed_data['updated_at'].replace('Z', '+00:00'))
        if 'start_date' in parsed_data and isinstance(parsed_data['start_date'], str):
            parsed_data['start_date'] = datetime.fromisoformat(parsed_data['start_date'].replace('Z', '+00:00'))
        if 'end_date' in parsed_data and isinstance(parsed_data['end_date'], str):
            parsed_data['end_date'] = datetime.fromisoformat(parsed_data['end_date'].replace('Z', '+00:00'))
        if 'application_deadline' in parsed_data and isinstance(parsed_data['application_deadline'], str):
            parsed_data['application_deadline'] = datetime.fromisoformat(parsed_data['application_deadline'].replace('Z', '+00:00'))
        
        return Opportunity(**parsed_data)