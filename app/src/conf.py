this_year = 2025
last_year = 2024
# day finish registration
given_date_str = "2025-06-09"
# Path to the input data folder
input_data_folder = "csm_data"
# outpout data folder
output_csv_folder = "csv"
# output data folder
output_data_folder = "output"
# Batch data folder
batch_data_folder = "batch"
# classification data folder
classification_data_folder = "classification"
# file examples
cat_examples_json = "cat_examples.json"
# Path to the registration data file
regdata = "Registration_data_csm.json"
regdata_refresh = "registration_combined_output.json"
# path to Demographic Data
demodata = "demographics_combined_output.json"
# Path to the seminars reference file
seminar_reference_24 = "tech london 2024 seminars reference.csv"
seminar_reference_25 = "tech london 2025 seminars reference.csv"
# Path to the seminars reference file
badge_scan_24 = "tech london 2024 seminars.csv"
badge_scan_25 = "tech london 2025 seminars.csv"
# Column with the registration date
date_column = "RegistrationDate"
# registration output
registration_this_year = "df_reg_25.csv"
registration_2025_full = "registration_2025_full.csv"
registration_2025 = "registration_2025.csv"
registration_data_json = "registration_data.json"
# Scan Data output
scans_data_24_25_enriched_csv = "scans_data_24_25_enriched.csv"
Registration_data_24_25_both_only_valid_badge_type_with_seminars = (
    "Registration_data_24_25_both_only_valid_badge_type_with_seminars.csv"
)
Registration_data_post_event_only_valid_badge_type_with_seminars = (
    "Registration_data_post_event_only_valid_badge_type_with_seminars.csv"
)
# Demographic Output
demographic_2025 = "demographic_2025.csv"
demographic_data_with_badge_json = "demographic_data_with_badge.json"
demographic_data_with_badge_json_full = "demographic_data_with_badge_full.json"
# Output merged_data
merged_data_json = "merged_data.json"
merged_data_status_json = "merged_data_status.json"
merged_data_list_key_json = "merged_data_list_key.json"
# Column to remove  from the registration data when Nan
reg_data_nan_columns = ["RegistrationDate", "Email", "ShowRef", "BadgeId"]
# Final columns to keep in the registration data
valid_columns = [
    "Email",
    "JobTitle",
    "Country",
    "BadgeType",
    "ShowRef",
    "BadgeId",
    "Source",
    "Days_since_registration",
]
# Shows to keep
shows_25 = ["BDAWL25", "CEEL25", "CCSEL25", "DCWL25", "DL25"]
shows_24 = ["DL24", "DCWL24", "CEEL24", "CCSEL24", "BDAWL24"]
badgeIDs_list = ["VIP", "Visitor"]  # , "Commercial Visitor"]

# Additional columns to exclude Registration Data
additional_columns_to_exclude = ["Email"]
# Bagedata columns
initial_columns_merge_visitor = [
    "Id",
    "Title",
    "Forename",
    "Surname",
    "Email",
    "Tel",
    "Mobile",
    "Fax",
    "Company",
    "JobTitle",
    "Addr1",
    "Addr2",
    "Addr3",
    "Town",
    "County",
    "Postcode",
    "Country",
    "Status",
    "BadgeType",
    "ShowRef_x",
    "RegistrationDate",
    "BadgeId_x",
    "RegCode",
    "Source",
    "Attended",
    "SegmentFromReg",
    "Upgrade",
    "Concatenated Seminar Names",
]
columns_merge_visitor_24_25 = [
    "Id",
    "Title",
    "Forename",
    "Surname",
    "Email",
    "Tel",
    "Mobile",
    "Fax",
    "Company",
    "JobTitle",
    "Addr1",
    "Addr2",
    "Addr3",
    "Town",
    "County",
    "Postcode",
    "Country",
    "Status",
    "BadgeType",
    "ShowRef",
    "RegistrationDate",
    "BadgeId",
    "RegCode",
    "Source",
    "Attended",
    "SegmentFromReg",
    "Upgrade",
    "Concatenated Seminar Names",
]

columns_merge_visitor_24_25_final = [
    "Email",
    "ShowRef",
    "BadgeId",
    "Concatenated Seminar Names",
]


# Concatenate Q&A Demografic Data
list_no = [
    "i have read and accept the event terms and conditions",
    "i have read and accept the privacy policy",
    "accessibility what can we do to make this event space more comfortable for you",
]
list_vip = [
    "what best describes your reason for attending i am attending because my company is",
    "decision making power",
]


nomenclature = {
    "Networking": "Networking: In this group are visitors who are currently focused primarily on building professional or personal relationships and expanding their network. They attend this event to meet industry peers, experts, and potential partners. Their interactions are more about establishing connections than gathering information, purchasing or buying. They value personal interactions and opportunities for collaboration. These visitors would be more interested in other opportunities such as speaking or meeting other visitors, and also likely to attend multiple co-located shows. On average 3 of every 10 profiles should be allocated to this category.",
    "Learning": "Learning: These attendees are currently motivated by educational and learning opportunities. They seek to gain new insights, learn about industry trends, and enhance their knowledge and skills. They are likely to attend workshops, seminars, and keynote speeches. Their interest in products or services is secondary to their desire for professional development. These visitors are interested on any extra information or content provided to them, and also likely to attend other co-located shows. They are less likely to come from far or pay for flights or hotel to attend the event. On average 3 of every 10 profiles should be allocated to this category.",
    "Searching": "The visitors are currently interested in searching for information on products and vendor (this means gathering as much information as possible on products, services, vendors or providers available at the event). Individuals in this category might have identified a need or a problem to solve but are still exploring what products, services, vendors or providers that can meet their specific requirements. Their primary goal is to collect as much information as possible without a strong inclination towards immediate purchasing. They may be open to conversations about products or services, but are not yet ready to engage on purchasing conversations. They might have many areas of interest and are likely to engage with multiple vendors to compare offerings, gather brochures, and ask general questions. On average 2 of every 10 profiles should be allocated to this category.",
    "Early_Purchasing_Intention": "Early Purchasing Intention: Attendees in this group are actively engaged in the sourcing process. They know well the type of product or service they require and might have narrowed down their options and are delving deeper into specific products or services, hence they have a small and well-defined set of main areas of interest. Their interactions are more detailed, involving discussions about pricing, implementation, or customization. They are seeking to understand how different offerings stack up against each other and may be forming preferences for vendor selection. However, they are not on the final stages of this purchase process. They are more likely to have a job title or function in procurement or purchasing positions, and this segment cannot include anyone in any sales job or position. On average, 1 of every 10 profiles should be allocated to this category.",
    "High_Purchase_Intention": "High Purchase Intention: This group represents delegates who are at the final stages of their purchasing journey. They have all the information they need and are making final evaluations to choose a vendor. Their interactions are decisive, focusing on final terms, delivery, support, and other post-purchase considerations. Engagements with these individuals are very relevant and time-critical as they are on the verge of making a purchase decision and they are going for a clear mission to confirm their information, hence not interested in becoming a speaker or exhibitor. They are less likely to be attending more than one of the other co-located shows. As they know what they are looking for (hence well-defined and narrow main areas of interest), they are more likely to have researched and initiated the visit by their own initiative searching for it on Google or other search engines, or being recommended by someone else, and much less likely to have known about the event from any type of advertising (emails Banners, direct mail social media or telemarketing). They are also more likely to hold senior positions in their companies with decision making power, and this segment cannot include anyone in any job or position related to sales. If a visitor reports no influence in purchasing decisions as their Decision making power, they should not be allocated to category. On average, less that 1 out of every 10 profiles should be allocated to this category.",
}

key_questions_demographic = [
    "job function",
    "what best describes your reason for attending i am attending because my company is",
    "decision making power",
    "which colocated events are of high relevance to you",
    "would you be interested in exhibiting sponsorship partnership speaking",
    "if you would like to receive information from us about third party products events and services please tick here",
    "how did you hear about us",
    "how do you plan to travel to the event",
    "how many nights do you intend to stay at a hotel for when attending this event",
]

questions_2025 = [
    "utmsource",
    "utmmedium",
    "utmcampaign",
    "job level",
    "job function",
    "i have read and accept the event terms and conditions",
    "i have read and accept the privacy policy",
    "if you would like to receive information from us about third party products events and services please tick here",
    "if you are happy for your name and email address to be shared with such third parties for marketing purposes please tick here",
    "what best describes your reason for attending i am attending because my company is",
    "decision making power",
    "number of employees",
    "where does your company operate out of",
    "your industry sector",
    "please specify your industry sector technology",
    "your main areas of interest",
    "which colocated events are of high relevance to you",
    "do you intend to visit",
    "would you be interested in exhibiting sponsorship partnership speaking",
    "would you be interested in subscribing to our official publications",
    "how did you hear about us",
    "how do you plan to travel to the event",
    "how many nights do you intend to stay at a hotel for when attending this event",
    "please specify your industry sector banking finance",
    "please specify your industry sector corporate",
    "which best describes your company",
    "please specify your industry sector retail",
    "would you be interested in hearing more from our partners",
    "twitter id",
    "please specify your industry sector media communications",
    "please specify your industry sector transportation",
    "accessibility what can we do to make this event space more comfortable for you",
    "please ensure that you have consent from your colleagues to register on behalf of them and provide their details to access the event and or other relevant services",
    "please specify your industry sector healthcare pharma",
    "please specify your industry sector professional services",
    "please specify your industry sector construction",
    "referrer",
    "please specify your industry sector service",
    "please specify your industry sector not for profit",
    "please specify your industry sector consumer goods",
    "please specify your industry sector manufacturing",
    "please specify your industry sector education",
    "please specify your industry sector arts",
    "please specify your industry sector cloud industry",
    "please specify your industry sector central local government",
    "which colocated events are of high relevance to you ccsl",
    "are you a member of any of the following associations",
    "interested in keeping up with the latest tech news",
    "linkedin id",
    "would you be interested in hearing more from our partner associations",
    "please specify your industry sector media entertainment",
    "does your company currently use devops tools and practices",
    "please specify your industry sector banking finance insurance",
    "keep in touch share your linkedin profile",
    "does your company operate a data centre",
    "does your company operate out of more than one site",
    "is your company looking to",
    "is your company looking to build a new data centre",
    "what are the hot topics in the market today and looking forwards to the future that data centre world should address in 2025",
    "would you be interested in subscribing to our official publication",
    "do you currently have a dedicated devops team and or infrastructure",
    "do you have a budget for devops solutions",
]
