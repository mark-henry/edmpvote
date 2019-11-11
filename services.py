from protorpc.wsgi import service

import app.edmpvote as edmpvote

# Map the RPC service and path (/GetService)
app = service.service_mappings([('/GetService', edmpvote.GetService)])