// Import the registration function
import { registerTool } from './index.js';

// Import tool classes
import { UserCredentialsTool } from './oauth/getUserDetailsTool.js';
import { ObjectListTool } from './objects/listObjectsTool.js';
import { ObjectSearchTool } from './objects/searchObjectsTool.js';
import { BatchReadObjectsTool } from './objects/batchReadObjectsTool.js';
import { BatchCreateObjectsTool } from './objects/batchCreateObjectsTool.js';
import { BatchUpdateObjectsTool } from './objects/batchUpdateObjectsTool.js';
import { GetSchemasTool } from './objects/getSchemaTool.js';
import { PropertiesListTool } from './properties/listPropertiesTool.js';
import { GetPropertyTool } from './properties/getPropertyTool.js';
import { CreateEngagementTool } from './engagements/createEngagementTool.js';
import { GetEngagementTool } from './engagements/getEngagementTool.js';
import { ObjectAssociationTool } from './associations/createAssociationTool.js';
import { AssociationsListTool } from './associations/listAssociationsTool.js';

// Register all tools
registerTool(new UserCredentialsTool());
registerTool(new ObjectListTool());
registerTool(new ObjectSearchTool());
registerTool(new BatchReadObjectsTool());
registerTool(new BatchCreateObjectsTool());
registerTool(new BatchUpdateObjectsTool());
registerTool(new GetSchemasTool());
registerTool(new PropertiesListTool());
registerTool(new GetPropertyTool());
registerTool(new CreateEngagementTool());
registerTool(new GetEngagementTool());
registerTool(new ObjectAssociationTool());
registerTool(new AssociationsListTool());