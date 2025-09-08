# 🚀 **SERAAJ SERVICE PORTS - SINGLE SOURCE OF TRUTH**

**⚠️ THIS IS THE CANONICAL PORT CONFIGURATION FOR ALL SERAAJ SERVICES**

## **Production Port Assignments**

| Service | Port | Module | Description |
|---------|------|--------|-------------|
| **BFF** | `8000` | `bff.main` | Backend-for-Frontend API Gateway |
| **Applications** | `8001` | `services.applications.api` | Event-sourced application management |
| **Matching** | `8003` | `services.matching.api` | ML-powered volunteer-opportunity matching |
| **Auth** | `8004` | `services.auth.api` | JWT authentication service |
| **Volunteers** | `8005` | `services.volunteers.api` | Volunteer profile management (STUB) |
| **Opportunities** | `8006` | `services.opportunities.api` | Opportunity catalog (STUB) |
| **Organizations** | `8007` | `services.organizations.api` | Organization management (STUB) |

## **Service URLs**

### **Health Check Endpoints**
```
BFF:           http://localhost:8000/api/health
Applications:  http://localhost:8001/health  
Matching:      http://localhost:8003/health
Auth:          http://localhost:8004/health
Volunteers:    http://localhost:8005/health
Opportunities: http://localhost:8006/health
Organizations: http://localhost:8007/health
```

### **API Documentation** 
```
BFF OpenAPI:    http://localhost:8000/docs
Applications:   http://localhost:8001/docs
Matching:       http://localhost:8003/docs
Auth:           http://localhost:8004/docs
```

## **Frontend Configuration**
```bash
# Environment Variable (REQUIRED)
NEXT_PUBLIC_BFF_URL=http://localhost:8000/api
```

## **Development Startup Commands**
```bash
# All services at once
python start_all_services.py

# Individual services
python -m bff.main                    # Port 8000
python -m services.applications.api   # Port 8001  
python -m services.matching.api       # Port 8003
python -m services.auth.api           # Port 8004
python -m services.volunteers.api     # Port 8005
python -m services.opportunities.api  # Port 8006
python -m services.organizations.api  # Port 8007
```

## **Docker Configuration**
```yaml
services:
  bff:           
    ports: ["8000:8000"]
  applications:  
    ports: ["8001:8001"]
  matching:      
    ports: ["8003:8003"]  
  auth:          
    ports: ["8004:8004"]
  volunteers:    
    ports: ["8005:8005"]
  opportunities: 
    ports: ["8006:8006"]
  organizations: 
    ports: ["8007:8007"]
```

## **❌ Port 8002 is RESERVED (unused)**
- Originally allocated for Matching service
- **DO NOT USE** - avoid conflicts with existing processes
- Matching service moved to 8003 for consistency

---

**🔒 FROZEN**: This configuration is locked for production stability.  
**📝 UPDATE RULE**: Any port changes require updating ALL references across:
- Service files (`*.py`)  
- Documentation (`*.md`)
- Configuration files
- Scripts and CI/CD pipelines
- Frontend environment variables

**📍 Last Updated**: August 11, 2025  
**📍 Status**: PRODUCTION READY