// Import the registration function
import { registerTool } from './index.js';

// Import tool classes
import { SearchTool } from './searchTool.js';
import { ReadWebpageTool } from './readWebpageTool.js';

// Register all tools
registerTool(new SearchTool());
registerTool(new ReadWebpageTool());