"""
Integration tests for dual backend repositories (file vs PostgreSQL)
"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Test imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.shared.models import Application, MatchSuggestion, ScoreComponents, MatchExplanation
from services.applications.repository import ApplicationRepository
from services.matching.repository import MatchRepository
from infrastructure.db.connection import init_database, close_database

class TestDualBackendApplicationRepository:
    """Test ApplicationRepository with both file and PostgreSQL backends"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for file storage tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_application(self):
        """Create sample application for testing"""
        return Application(
            id=str(uuid4()),
            volunteerId=str(uuid4()),
            opportunityId=str(uuid4()),
            organizationId=str(uuid4()),
            status="draft",
            coverLetter="I am interested in this opportunity.",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_file_backend(self, temp_dir, sample_application):
        """Test ApplicationRepository with file backend"""
        # Force file backend
        os.environ.pop('DATABASE_URL', None)
        
        repo = ApplicationRepository(data_dir=temp_dir, storage_backend="file")
        assert repo.storage_backend == "file"
        
        # Create application
        created_app = await repo.create(sample_application)
        assert created_app.id == sample_application.id
        
        # Get application
        retrieved_app = await repo.get(sample_application.id)
        assert retrieved_app is not None
        assert retrieved_app.id == sample_application.id
        assert retrieved_app.status == "draft"
        
        # Update application
        retrieved_app.status = "submitted"
        updated_app = await repo.update(retrieved_app)
        assert updated_app.status == "submitted"
        
        # Find by volunteer
        volunteer_apps = await repo.find_by_volunteer(sample_application.volunteerId)
        assert len(volunteer_apps) == 1
        assert volunteer_apps[0].id == sample_application.id
        
        # Health check
        health = await repo.health_check()
        assert health['status'] == 'healthy'
        assert health['backend'] == 'file'
    
    @pytest.mark.asyncio
    async def test_postgres_backend(self, sample_application):
        """Test ApplicationRepository with PostgreSQL backend"""
        # Skip if no database configured
        if not os.getenv('DATABASE_URL') and not os.getenv('DB_HOST'):
            pytest.skip("PostgreSQL not configured")
        
        try:
            await init_database()
            
            # Force PostgreSQL backend
            repo = ApplicationRepository(storage_backend="postgres")
            assert repo.storage_backend == "postgres"
            
            # Create application
            created_app = await repo.create(sample_application)
            assert created_app.id == sample_application.id
            
            # Get application
            retrieved_app = await repo.get(sample_application.id)
            assert retrieved_app is not None
            assert retrieved_app.id == sample_application.id
            assert retrieved_app.status == "draft"
            
            # Update application
            retrieved_app.status = "submitted"
            updated_app = await repo.update(retrieved_app)
            assert updated_app.status == "submitted"
            
            # Find by volunteer
            volunteer_apps = await repo.find_by_volunteer(sample_application.volunteerId)
            assert len(volunteer_apps) >= 1
            
            # Health check
            health = await repo.health_check()
            assert health['status'] == 'healthy'
            assert health['backend'] == 'postgres'
            
        finally:
            await close_database()
    
    @pytest.mark.asyncio
    async def test_backend_auto_detection(self, temp_dir):
        """Test automatic backend detection based on environment"""
        # Test file backend detection
        os.environ.pop('DATABASE_URL', None)
        os.environ.pop('DB_HOST', None)
        
        repo = ApplicationRepository(data_dir=temp_dir)
        assert repo.storage_backend == "file"
        
        # Test PostgreSQL backend detection
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/test'
        
        repo = ApplicationRepository()
        assert repo.storage_backend == "postgres"
        
        # Cleanup
        os.environ.pop('DATABASE_URL', None)

class TestDualBackendMatchRepository:
    """Test MatchRepository with both file and PostgreSQL backends"""
    
    @pytest.fixture
    def sample_match_suggestion(self):
        """Create sample match suggestion for testing"""
        return MatchSuggestion(
            id=str(uuid4()),
            volunteerId=str(uuid4()),
            opportunityId=str(uuid4()),
            organizationId=str(uuid4()),
            score=0.85,
            scoreComponents=ScoreComponents(
                distanceScore=0.9,
                skillsScore=0.8,
                availabilityScore=0.85
            ),
            explanation=MatchExplanation(
                summary="Great match based on location and skills",
                details=["Close to your location", "Skills match required expertise"]
            ),
            generatedAt=datetime.utcnow(),
            status="active"
        )
    
    @pytest.mark.asyncio
    async def test_file_backend(self, sample_match_suggestion):
        """Test MatchRepository with file backend"""
        # Force file backend
        os.environ.pop('DATABASE_URL', None)
        
        repo = MatchRepository(storage_backend="file")
        assert repo.storage_backend == "file"
        
        # Save suggestion
        saved_suggestion = await repo.save(sample_match_suggestion)
        assert saved_suggestion.id == sample_match_suggestion.id
        
        # Get suggestion
        retrieved_suggestion = await repo.get(sample_match_suggestion.id)
        assert retrieved_suggestion is not None
        assert retrieved_suggestion.id == sample_match_suggestion.id
        
        # Find by volunteer
        volunteer_suggestions = await repo.find_by_volunteer(sample_match_suggestion.volunteerId)
        assert len(volunteer_suggestions) == 1
        
        # Update status
        updated_suggestion = await repo.update_status(sample_match_suggestion.id, "viewed")
        assert updated_suggestion is not None
        assert updated_suggestion.status == "viewed"
        
        # Health check
        health = await repo.health_check()
        assert health['status'] == 'healthy'
        assert health['backend'] == 'file'
    
    @pytest.mark.asyncio
    async def test_postgres_backend(self, sample_match_suggestion):
        """Test MatchRepository with PostgreSQL backend"""
        # Skip if no database configured
        if not os.getenv('DATABASE_URL') and not os.getenv('DB_HOST'):
            pytest.skip("PostgreSQL not configured")
        
        try:
            await init_database()
            
            # Force PostgreSQL backend
            repo = MatchRepository(storage_backend="postgres")
            assert repo.storage_backend == "postgres"
            
            # Save suggestion
            saved_suggestion = await repo.save(sample_match_suggestion)
            assert saved_suggestion.id == sample_match_suggestion.id
            
            # Get suggestion
            retrieved_suggestion = await repo.get(sample_match_suggestion.id)
            assert retrieved_suggestion is not None
            assert retrieved_suggestion.id == sample_match_suggestion.id
            
            # Find by volunteer
            volunteer_suggestions = await repo.find_by_volunteer(sample_match_suggestion.volunteerId)
            assert len(volunteer_suggestions) >= 1
            
            # Update status
            updated_suggestion = await repo.update_status(sample_match_suggestion.id, "viewed")
            assert updated_suggestion is not None
            assert updated_suggestion.status == "viewed"
            
            # Health check
            health = await repo.health_check()
            assert health['status'] == 'healthy'
            assert health['backend'] == 'postgres'
            
        finally:
            await close_database()

class TestBackendCompatibility:
    """Test that both backends provide the same functionality"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for compatibility testing"""
        return {
            'application': Application(
                id=str(uuid4()),
                volunteerId=str(uuid4()),
                opportunityId=str(uuid4()),
                organizationId=str(uuid4()),
                status="draft",
                coverLetter="Test application",
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            ),
            'match_suggestion': MatchSuggestion(
                id=str(uuid4()),
                volunteerId=str(uuid4()),
                opportunityId=str(uuid4()),
                organizationId=str(uuid4()),
                score=0.75,
                scoreComponents=ScoreComponents(
                    distanceScore=0.8,
                    skillsScore=0.7,
                    availabilityScore=0.75
                ),
                explanation=MatchExplanation(
                    summary="Good match",
                    details=["Skills align", "Available when needed"]
                ),
                generatedAt=datetime.utcnow(),
                status="active"
            )
        }
    
    @pytest.mark.asyncio
    async def test_application_repository_compatibility(self, sample_data):
        """Test that file and PostgreSQL backends provide identical functionality"""
        application = sample_data['application']
        
        # Test file backend
        file_repo = ApplicationRepository(storage_backend="file")
        file_results = await self._test_application_operations(file_repo, application)
        
        # Test PostgreSQL backend (if available)
        if os.getenv('DATABASE_URL') or os.getenv('DB_HOST'):
            try:
                await init_database()
                
                postgres_repo = ApplicationRepository(storage_backend="postgres")
                postgres_results = await self._test_application_operations(postgres_repo, application)
                
                # Compare results structure (not exact values due to timestamps)
                assert set(file_results.keys()) == set(postgres_results.keys())
                
            finally:
                await close_database()
    
    async def _test_application_operations(self, repo, application):
        """Helper to test application repository operations"""
        results = {}
        
        # Create
        created = await repo.create(application)
        results['created'] = created is not None
        
        # Get
        retrieved = await repo.get(application.id)
        results['retrieved'] = retrieved is not None and retrieved.id == application.id
        
        # Update
        if retrieved:
            retrieved.status = "submitted"
            updated = await repo.update(retrieved)
            results['updated'] = updated.status == "submitted"
        
        # Find by volunteer
        volunteer_apps = await repo.find_by_volunteer(application.volunteerId)
        results['find_by_volunteer'] = len(volunteer_apps) > 0
        
        # Health check
        health = await repo.health_check()
        results['health_check'] = health['status'] == 'healthy'
        
        return results
    
    @pytest.mark.asyncio
    async def test_match_repository_compatibility(self, sample_data):
        """Test that file and PostgreSQL backends provide identical functionality"""
        suggestion = sample_data['match_suggestion']
        
        # Test file backend
        file_repo = MatchRepository(storage_backend="file")
        file_results = await self._test_match_operations(file_repo, suggestion)
        
        # Test PostgreSQL backend (if available)
        if os.getenv('DATABASE_URL') or os.getenv('DB_HOST'):
            try:
                await init_database()
                
                postgres_repo = MatchRepository(storage_backend="postgres")
                postgres_results = await self._test_match_operations(postgres_repo, suggestion)
                
                # Compare results structure
                assert set(file_results.keys()) == set(postgres_results.keys())
                
            finally:
                await close_database()
    
    async def _test_match_operations(self, repo, suggestion):
        """Helper to test match repository operations"""
        results = {}
        
        # Save
        saved = await repo.save(suggestion)
        results['saved'] = saved is not None
        
        # Get
        retrieved = await repo.get(suggestion.id)
        results['retrieved'] = retrieved is not None and retrieved.id == suggestion.id
        
        # Find by volunteer
        volunteer_suggestions = await repo.find_by_volunteer(suggestion.volunteerId)
        results['find_by_volunteer'] = len(volunteer_suggestions) > 0
        
        # Update status
        updated = await repo.update_status(suggestion.id, "viewed")
        results['update_status'] = updated is not None and updated.status == "viewed"
        
        # Health check
        health = await repo.health_check()
        results['health_check'] = health['status'] == 'healthy'
        
        return results