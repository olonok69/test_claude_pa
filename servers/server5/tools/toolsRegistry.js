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
import { CreatePropertyTool } from './properties/createPropertyTool.js';
import { UpdatePropertyTool } from './properties/updatePropertyTool.js';
import { CreateEngagementTool } from './engagements/createEngagementTool.js';
import { GetEngagementTool } from './engagements/getEngagementTool.js';
import { UpdateEngagementTool } from './engagements/updateEngagementTool.js';
import { ObjectAssociationTool } from './associations/createAssociationTool.js';
import { AssociationsListTool } from './associations/listAssociationsTool.js';
import { AssociationSchemaDefinitionTool } from './associations/getAssociationDefinitionsTool.js';
import { WorkflowsListTool } from './workflows/listWorkflowsTool.js';
import { GetWorkflowTool } from './workflows/getWorkflowTool.js';
import { GetHubspotLinkTool } from './links/getHubspotLinkTool.js';
import { FeedbackLinkTool } from './links/feedbackLinkTool.js';

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
registerTool(new CreatePropertyTool());
registerTool(new UpdatePropertyTool());
registerTool(new CreateEngagementTool());
registerTool(new GetEngagementTool());
registerTool(new UpdateEngagementTool());
registerTool(new ObjectAssociationTool());
registerTool(new AssociationsListTool());
registerTool(new AssociationSchemaDefinitionTool());
registerTool(new WorkflowsListTool());
registerTool(new GetWorkflowTool());
registerTool(new GetHubspotLinkTool());
registerTool(new FeedbackLinkTool());