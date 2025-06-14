// https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm#object-type-ids
export const HUBSPOT_OBJECT_TYPES = [
    'appointments',
    'companies',
    'contacts',
    'courses',
    'deals',
    'leads',
    'line_items',
    'listings',
    'marketing_events',
    'meetings',
    'orders',
    'postal_mail',
    'products',
    'quotes',
    'services',
    'subscriptions',
    'tickets',
    'users',
];

export default HUBSPOT_OBJECT_TYPES;

export const HUBSPOT_OBJECT_TYPE_TO_ID = {
    appointments: '0-421',
    calls: '0-48',
    communications: '0-18',
    companies: '0-2',
    contacts: '0-1',
    courses: '0-410',
    deals: '0-3',
    emails: '0-49',
    leads: '0-136',
    line_items: '0-8',
    listings: '0-420',
    marketing_events: '0-54',
    meetings: '0-47',
    notes: '0-46',
    orders: '0-123',
    postal_mail: '0-116',
    products: '0-7',
    quotes: '0-14',
    services: '0-162',
    subscriptions: '0-69',
    tasks: '0-27',
    tickets: '0-5',
    users: '0-115',
};

export const HUBSPOT_ID_TO_OBJECT_TYPE = Object.entries(HUBSPOT_OBJECT_TYPE_TO_ID).reduce((acc, [objectType, id]) => ({
    ...acc,
    [id]: objectType,
}), {});