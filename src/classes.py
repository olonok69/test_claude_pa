from typing import  Dict, Literal, Tuple

from langchain_core.output_parsers import PydanticOutputParser

from pydantic import BaseModel


class Labels_Nomenclature(BaseModel):
    label: Literal[
        "Networking",
        "Learning",
        "searching_info_on_products_and_vendors",
        "early_purchasing_intention",
        "high_purchasing_intention",
    ]


class Score_Nomenclature(BaseModel):
    score: Literal["High Confidence", "Mid-Level Confidence", "Low Confidence"]


class Visitor_Nomenclature_Class(BaseModel):
    label: Dict[Labels_Nomenclature, Score_Nomenclature]


class Top_K_Label(BaseModel):
    pos: Literal["1", "2", "3", "4", "5"]


class Top_K(BaseModel):
    top_k: Dict[Top_K_Label, Labels_Nomenclature]


class ValueModel(BaseModel):
    nomemclature: Visitor_Nomenclature_Class
    topk: Top_K


class Visitor_Classification(BaseModel):
    """Information about a the Visitor."""

    classification: Dict[Tuple[Visitor_Nomenclature_Class, Top_K], ValueModel]


from pydantic import BaseModel, Field


class Deep_Seek_PromptTemplate:
    def __init__(self):
        self.base_template = """A conversation between User and Assistant. The user asks a question, and the Assistant solves it.
The assistant first thinks about the reasoning process in the mind and then provides the user with the answer.
The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively.

User: {question}
Assistant: {think_tag}
{reasoning}
{think_end_tag}
{answer_tag}
{solution}
{answer_end_tag}
"""

    def generate_math_prompt(self, question):
        """Generate a prompt for mathematical problems"""
        return self.base_template.format(
            question=question,
            think_tag="<think>",
            reasoning="""1. First, let's understand what the question is asking
2. Break down the mathematical components
3. Apply relevant mathematical rules
4. Calculate step by step
5. Verify the result""",
            think_end_tag="</think>",
            answer_tag="<answer>",
            solution="[Mathematical solution will be provided here]",
            answer_end_tag="</answer>",
        )

    def generate_code_prompt(self, question):
        """Generate a prompt for coding problems"""
        return self.base_template.format(
            question=question,
            think_tag="<think>",
            reasoning="""1. Analyze the programming requirements
2. Consider edge cases and constraints
3. Plan the algorithm structure
4. Think about time and space complexity
5. Consider test cases""",
            think_end_tag="</think>",
            answer_tag="<answer>",
            solution="[Code solution will be provided here]",
            answer_end_tag="</answer>",
        )

    def generate_reasoning_prompt(self, question):
        """Generate a prompt for solving reasoning problems"""
        return self.base_template.format(
            question=question,
            think_tag="<think>",
            reasoning="""1. Analyze the question and identify the reasoning process
2. Break down the reasoning components
3. Apply relevant reasoning rules
4. Calculate step by step
5. Verify the result""",
            think_end_tag="</think>",
            answer_tag="<answer>",
            solution="[the solution will be provided here]",
            answer_end_tag="</answer>",
        )


class Phi3_PromptTemplate:
    def __init__(self, nomenclature, examples):
        self.nomenclature = nomenclature
        self.examples = examples
        self.parser = PydanticOutputParser(pydantic_object=Visitor_Classification)
        self.base_template = """{system_start}You are a clever classifier assessing to which category each Event Visitor belong to one out of the 5 categories in section CATEGORIES.
        The format of each category is Category = Description of this category.
        You will be provided with an example of profile of each category on the section EXAMPLES. 
        The format of each example is Category = Profile of this category.
        
        CATEGORIES
        ----------
        {categories}
        ------------
        
        EXAMPLES
        --------
        {examples}
        ----------
        
        Intructions to classify the Profile:
        --------------
        {reasoning}
        {system_ends}
        
        {start_user}Profile to Classify: {profile}{end_user}{assistant_tag}

"""

    def generate_nomemclature(self):
        return "\n".join(
            [f"{key} = {value}\n" for key, value in self.nomenclature.items()]
        )

    def generate_examples(self):
        return "\n".join([f"{key} = {value}\n" for key, value in self.examples.items()])

    def generate_keys(self):
        return list(self.examples.keys())

    def format_instructions(self):
        return self.parser.get_format_instructions()

    def generate_clustering_prompt(self, profile):
        """Generate a prompt for solving reasoning problems"""
        return self.base_template.format(
            profile=profile,
            system_start="<|system|>",
            system_ends="<|end|>",
            categories=self.generate_nomemclature(),
            examples=self.generate_examples(),
            reasoning=f"""
                        1. Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        2. JobTitle, Job Level , Size of the company, Number of Employees, Number of Days in Hotel, can give you an Idea of how much interest has the visitor to come to the Event
                        3. Select 1 of the 5 choices in this list {self.generate_keys()} for each profile provided. Provide a confidence score based in one of these 3 classes. "High Confidence", "Mid-Level Confidence" and  "Low Confidence". 
                            No additional Preamble, explanation or comments for the selection or the score. Stick exactly to the labels provided.
                        4. Based in your Choice in step 3, return an allocation to all of the 5 classes sorted from the most likely (the one you choose in step 3) to the less likely in a dictionary,
                         the dictionary will contain a key per class = key : class description, where key is the position on the rank and class description is one among the list {self.generate_keys()}.
                         Here for this step again, No additional Preamble, explanation or comments for the selection or the score. Stick exactly to the labels and format provided
                        5. Return a json with the class for this profile, the confidence score and the sorted classes in a list. No preamble or explanation, or additional comments.
                        
                        THIS IS AN EXAMPLE OF, no what you has to return each time:
                        {{"searching_info_on_products_and_vendors" : "High Confidence", 
                                    "top_k": {{"1":"searching_info_on_products_and_vendors',
                                            "2":'Networking',
                                            "3" :'Learning',
                                            "4" :'early_purchasing_intention',
                                            "5":'high_purchasing_intention'}}}}.
                        6. Only return the Json. Very Important. No additional Preamble, explanation or comments.""",
            start_user="<|user|>",
            end_user="<|end|>",
            assistant_tag="<|assistant|>",
        )


class LLama_PromptTemplate_bis:

    def __init__(self, nomenclature, examples):
        self.nomenclature = nomenclature
        self.examples = examples
        self.base_template_with_examples = """{begin_text}{start_header_id}system{end_header_id}
        You are an expert classifier assessing profiles of visitors registered to a Technology event. Your task is to assess the input data for each visitor and rank from 1 to 5 the categories according to the most to the lest likely that each visitor is likely to be allocated to.

        Also provide an assessment of the level of confidence of the choice of the category that the visitor is allocated to (this is the category number 1 in the output),

        You will be provided with a few examples of profiles that belong to each category in the section EXAMPLES. The format of each example is Category = Profile of this category.

        Return the following outputs for these profiles in a string and no preamble or explanation.

        Outputs to return as a string for each profile provided:

        1. Profile identifier,

        2. A ranked list from 1 to 5 of each of the category classes, from most likely class on number 1 to less likely class in number 5.

        3. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”.
        
        CATEGORIES
        ----------
        {categories}
        ------------
        
        EXAMPLES
        --------
        {examples}
        ----------
        
        Intructions to classify the Profile:
        -----------------
        {reasoning}
        -----------------
        
        Intructions OUTPUT
        ------------------
        {output}
        -----------------
        
        Profile to Classify: {profile} 
        {eot_id}{start_header_id}assistant{end_header_id}

"""
        self.base_template_without_examples = """{begin_text}{start_header_id}system{end_header_id}You are a clever classifier assessing to which category each Event Visitor belong to,
        out of the 5 categories in section CATEGORIES. The format of each category is Category = Description of this category.
       
        CATEGORIES
        ----------
        {categories}
        ------------
        
        Intructions to classify the Profile:
        --------------
        {reasoning}
        --------------
        
        Intructions OUTPUT
        ------------------
        {output}
        -----------------
        
        Profile to Classify: {profile} 
        {eot_id}{start_header_id}assistant{end_header_id}

"""

    def generate_nomemclature(self):
        return "\n".join(
            [f"{key} = {value}\n" for key, value in self.nomenclature.items()]
        )

    def generate_examples(self):
        return "\n".join([f"{key} = {value}\n" for key, value in self.examples.items()])

    def generate_keys(self):
        return list(self.examples.keys())

    def generate_clustering_prompt(
        self, profile, profile_id, include_examples: bool = True
    ):
        """Generate a prompt for getting Visitor Classification"""
        if include_examples:
            return self.base_template_with_examples.format(
                profile=profile,
                profile_id=profile_id,
                begin_text="<|begin_of_text|>",
                start_header_id="<|start_header_id|>",
                end_header_id="<|end_header_id|>",
                categories=self.generate_nomemclature(),
                examples=self.generate_examples(),
                reasoning=f"""1. for each profile provided, you have to allocate the visitor to one of the 5 categories provided in the section CATEGORIES. list of possible categories is {self.generate_keys()}.
                        2. provide a ranking from 1 to 5 of the categories, from the most likely to the less likely that the visitor is allocated to.
                        3. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”
                        4. Think Step by Step.
                        """,
                output=f"""
                        Prepare the output with the folowwing Instructions
                            - Have to be a Dictionary/JSON.
                            - Only return the Json. Very Important. No additional Preamble, explanation or comments.
                        example of the output:
                        {{
                            "profile_id": {{profile_id}},
                            "ranked_categories": ["Networking", "Learning", "Searching", "Early Purchasing Intention", "High Purchasing Intention"],
                            "certainty": "Very certain"
                        }}
                        """,
                eot_id="<|eot_id|>",
            )
        else:
            return self.base_template_without_examples.format(
                profile=profile,
                profile_id=profile_id,
                begin_text="<|begin_of_text|>",
                start_header_id="<|start_header_id|>",
                end_header_id="<|end_header_id|>",
                categories=self.generate_nomemclature(),
                reasoning=f"""1. Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        2. JobTitle, Job Level , Size of the company, Number of Employees, Number of Days in Hotel, can give you an Idea of how much interest has the visitor to come to the Event
                           for some visitor we have Information about what they visit last year. This in after the text "Attended seminars in 2024".
                        3. Select 1 of the 5 choices in this list {self.generate_keys()} for each profile provided. Provide a confidence score based in 1 of this 3 classes. "High Confidence", "Mid-Level Confidence" and  "Low Confidence".
                        4. Based in your Choice in step 3, return an allocation to all of the 5 classes sorted from the most likely (the one you choose in step 3) to the less likely in a dictionary,
                         the dictionary will contain a key per class = key : class description, where key is the position on the rank and class description is one among the list {self.generate_keys()}
                        5. Return a json like the example bellow with two dictionaries to complete step 3 and 4. No preamble or explanation, or additional comments.
                        
                        THIS IS AN EXAMPLE OF, no what you has to return every time:
                                {{
                                    "searching_info_on_products_and_vendors" : "High Confidence", 
                        
                                    "top_k": {{
                                            "1": "searching_info_on_products_and_vendors",
                                            "2": "Networking",
                                            "3": "Learning",
                                            "4": "early_purchasing_intention",
                                            "5": "high_purchasing_intention"
                                            }}
                                }}
                                            
                        6. Only return the Json. Very Important. No additional Preamble, explanation or comments.
                        """,
                eot_id="<|eot_id|>",
            )


class LLama_PromptTemplate:
    def __init__(self, nomenclature, examples):
        self.nomenclature = nomenclature
        self.examples = examples
        self.llama_template = """<<SYS>> \n  You are an expert classifier assessing profiles of visitors registered to a Technology event. Your task is to assess the input data for each visitor and rank from 1 to 5 the categories according to the most to the lest likely that each visitor is likely to be allocated to. \n 
        You will be provided with a few examples of profiles that belong to each category in the section EXAMPLES. The format of each example is Category = Profile of this category.

        Also, provide an assessment of the level of confidence of the choice of the category that the visitor is allocated to (this is the category number 1 in the output), based on data completion and how well each profile fits with the description and examples of the top category allocated.

        Return the following outputs for these profiles in a string and no preamble or explanation.

        Outputs to return as a string for each profile provided:

        1. A ranked list from 1 to 5 of each of the category classes, from most likely class on number 1 to less likely class in number 5.

        2. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”. Only use the labels with “certain” if the profile matches the description and examples extremely closely.

        CATEGORIES
        ----------
        {categories}
        ------------
        
        EXAMPLES
        --------
        {examples}
        ----------
        
        Intructions to classify the Profile:
        -----------------
        {reasoning}
        -----------------
        
        Intructions OUTPUT
        ------------------
        {output}
        -----------------
        """

        self.base_template_with_examples = """{begin_text}{start_header_id}system{end_header_id}
        You are an expert classifier assessing profiles of visitors registered to a Technology event. Your task is to assess the input data for each visitor and rank from 1 to 5 the categories according to the most to the lest likely that each visitor is likely to be allocated to.

        You will be provided with a few examples of profiles that belong to each category in the section EXAMPLES. The format of each example is Category = Profile of this category.

        Also, provide an assessment of the level of confidence of the choice of the category that the visitor is allocated to (this is the category number 1 in the output), based on data completion and how well each profile fits with the description and examples of the top category allocated.

        Return the following outputs for these profiles in a string and no preamble or explanation.

        Outputs to return as a string for each profile provided:

        1. A ranked list from 1 to 5 of each of the category classes, from most likely class on number 1 to less likely class in number 5.

        2. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”. Only use the labels with “certain” if the profile matches the description and examples extremely closely.

        CATEGORIES
        ----------
        {categories}
        ------------
        
        EXAMPLES
        --------
        {examples}
        ----------
        
        Intructions to classify the Profile:
        -----------------
        {reasoning}
        -----------------
        
        Intructions OUTPUT
        ------------------
        {output}
        -----------------
        
        Profile to Classify: {profile} 
        {eot_id}{start_header_id}assistant{end_header_id}

"""
        self.base_template_without_examples = """{begin_text}{start_header_id}system{end_header_id}You are a clever classifier assessing to which category each Event Visitor belong to,
        out of the 5 categories in section CATEGORIES. The format of each category is Category = Description of this category.
       
        CATEGORIES
        ----------
        {categories}
        ------------
        Intructions to classify the Profile:
        {reasoning}
        Profile to Classify: {profile} 
        {eot_id}{start_header_id}assistant{end_header_id}

"""

    def generate_nomemclature(self):
        return "\n".join(
            [f"{key} = {value}\n" for key, value in self.nomenclature.items()]
        )

    def generate_examples_old(self):
        return "\n".join([f"{key} = {value}\n" for key, value in self.examples.items()])

    def generate_examples(self):
        output_text = ""
        for item in self.examples:
            category = item["category"]
            input_str = item["input"]

            output_text += f"{category}:\n"  # Add the category as a heading

            lines = input_str.splitlines()  # Split input string into lines
            for line in lines:
                if line:  # check if the line is empty
                    try:
                        key, value = line.split(
                            ":", 1
                        )  # Split each line into key and value
                        output_text += (
                            f"{key.strip()} = {value.strip()}\n"  # Add to output
                        )
                    except ValueError:  # Handle lines without a colon
                        output_text += (
                            f"{line.strip()}\n"  # add the line without key and value
                        )
            output_text += "\n"  # Add an extra newline for separation

        return output_text

    def generate_keys(self):
        return list(self.nomenclature.keys())

    def generate_llama_prompt(self):
        """Generate a prompt for getting Visitor Classification"""
        system_prompt = self.llama_template.format(
            categories=self.generate_nomemclature(),
            examples=self.generate_examples(),
            reasoning=f"""1. For each profile provided, you have to allocate the visitor to one of the 6 categories provided in the section CATEGORIES. List of possible categories to allocate the profile {self.generate_keys()}.
                        2. Important: Early Purchasing Intention and High Purchase Intention segments cannot include anyone in any job or position related to sales.
                        3. Provide a ranking from 1 to 5 of the categories, from the most likely to the less likely that the visitor is allocated to.
                        4. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”
                        5. Use the answers to the Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        6. Think stpe by step.
                        """,
            output=f"""
                        Prepare the output with the folowwing Instructions
                            - Have to be a Dictionary/JSON. with 3 keys: category, ranked_categories, certainty
                                - category: the category that the profile is allocated to possible values {self.generate_keys()}
                                - ranked_categories: a list of the categories from the most likely to the less likely that the visitor is allocated to. Only the categories that the profile is allocated to, no scores or confidence levels. the first element must be the category that the profile is allocated to. The ranked list must contains 5 elements.
                                - certainty: the level of confidence of the choice of the category that the visitor is allocated to (this is the category number 1 in the output), using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”
                            - Only return the Json. Very Important. No additional Preamble, explanation or comments.

                        """,
        )

        return system_prompt

    def generate_clustering_prompt(self, profile, include_examples: bool = True):
        """Generate a prompt for getting Visitor Classification"""
        if include_examples:
            return self.base_template_with_examples.format(
                profile=profile,
                begin_text="<|begin_of_text|>",
                start_header_id="<|start_header_id|>",
                end_header_id="<|end_header_id|>",
                categories=self.generate_nomemclature(),
                examples=self.generate_examples(),
                reasoning=f"""1. for each profile provided, you have to allocate the visitor to one of the 6 categories provided in the section CATEGORIES. List of possible categories to allocate the profile {self.generate_keys()}.
                        2. provide a ranking from 1 to 5 of the categories, from the most likely to the less likely that the visitor is allocated to.
                        3. An assessment of how certain you are that the allocation is correct, in particular the allocation to the most likely category in position 1 on the output list, using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”
                        4. Think stpe by step.
                        """,
                output=f"""
                        Prepare the output with the folowwing Instructions
                            - Have to be a Dictionary/JSON. with 3 keys: category, ranked_categories, certainty
                                - category: the category that the profile is allocated to possible values {self.generate_keys()}
                                - ranked_categories: a list of the categories from the most likely to the less likely that the visitor is allocated to. Only the categories that the profile is allocated to, no scores or confidence levels. the first element must be the category that the profile is allocated to. The ranked list must contains 5 elements.
                                - certainty: the level of confidence of the choice of the category that the visitor is allocated to (this is the category number 1 in the output), using one of the following labels: “Very certain”, “Fairly certain”, “Likely but not certain to be correct” and “This allocation might or not be correct”
                            - Only return the Json. Very Important. No additional Preamble, explanation or comments.

                        """,
                eot_id="<|eot_id|>",
            )
        else:
            return self.base_template_without_examples.format(
                profile=profile,
                begin_text="<|begin_of_text|>",
                start_header_id="<|start_header_id|>",
                end_header_id="<|end_header_id|>",
                categories=self.generate_nomemclature(),
                reasoning=f"""1. Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        2. JobTitle, Job Level , Size of the company, Number of Employees, Number of Days in Hotel, can give you an Idea of how much interest has the visitor to come to the Event
                        3. Select 1 of the 5 choices in this list {self.generate_keys()} for each profile provided. Provide a confidence score based in 1 of this 3 classes. "High Confidence", "Mid-Level Confidence" and  "Low Confidence".
                        4. Based in your Choice in step 3, return an allocation to all of the 5 classes sorted from the most likely (the one you choose in step 3) to the less likely in a dictionary,
                         the dictionary will contain a key per class = key : class description, where key is the position on the rank and class description is one among the list {self.generate_keys()}
                        5. Return a json with the class for this profile, the confidence score and the sorted classes in a list. No preamble or explanation, or additional comments.
                        
                        THIS IS AN EXAMPLE OF, no what you has to return every time:
                                {{
                                    "searching_info_on_products_and_vendors" : "High Confidence", 
                        
                                    "top_k": {{
                                            "1": "searching_info_on_products_and_vendors",
                                            "2": "Networking",
                                            "3": "Learning",
                                            "4": "early_purchasing_intention",
                                            "5": "high_purchasing_intention"
                                            }}
                                }}
                        6. Only return the Json. Very Important. No additional Preamble, explanation or comments.
                        """,
                eot_id="<|eot_id|>",
            )
