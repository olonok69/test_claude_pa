import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import { BaseTool } from '../baseTool.js';
import HubSpotClient from '../../utils/client.js';
import { HUBSPOT_OBJECT_TYPES } from '../../types/objectTypes.js';

const AssociationSpecSchema = z.object({
    associationCategory: z.enum(['HUBSPOT_DEFINED', 'USER_DEFINED', 'INTEGRATOR_DEFINED']),
    associationTypeId: z.number().int().positive(),
});

const ObjectAssociationSchema = z.object({
    fromObjectType: z
        .string()
        .describe(`The type of HubSpot object to create association from. Valid values include: ${HUBSPOT_OBJECT_TYPES.join(', ')}. For custom objects, use the hubspot-get-schemas tool to get the objectType.`),
    fromObjectId: z.string().describe('The ID of the object to create association from'),
    toObjectType: z
        .string()
        .describe(`The type of HubSpot object to create association to. Valid values include: ${HUBSPOT_OBJECT_TYPES.join(', ')}. For custom objects, use the hubspot-get-schemas tool to get the objectType.`),
    toObjectId: z.string().describe('The ID of the object to create association to'),
    associations: z
        .array(AssociationSpecSchema)
        .min(1)
        .describe('List of association specifications defining the relationship'),
});

const ToolDefinition = {
    name: 'hubspot-create-association',
    description: `
    🛡️ Guardrails:
      1.  Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.

    🎯 Purpose:
      1. Establishes relationships between HubSpot objects, linking records across different object types, by creating an association between two objects.

    📋 Prerequisites:
      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId if you don't have that already.
      2. Use the hubspot-get-association-definitions tool to identify valid association types before creating associations.
  `,
    inputSchema: zodToJsonSchema(ObjectAssociationSchema),
    annotations: {
        title: 'Create CRM Object Association',
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
};

export class ObjectAssociationTool extends BaseTool {
    client;

    constructor() {
        super(ObjectAssociationSchema, ToolDefinition);
        this.client = new HubSpotClient();
    }

    async process(args) {
        try {
            const response = await this.client.put(`/crm/v4/objects/${args.fromObjectType}/${args.fromObjectId}/associations/${args.toObjectType}/${args.toObjectId}`, {
                body: args.associations,
            });

            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            fromObjectTypeId: response.fromObjectTypeId,
                            fromObjectId: response.fromObjectId,
                            toObjectTypeId: response.toObjectTypeId,
                            toObjectId: response.toObjectId,
                            labels: response.labels,
                        }, null, 2),
                    },
                ],
            };
        } catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Error creating HubSpot association: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    }
}