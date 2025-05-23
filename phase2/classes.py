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
            answer_end_tag="</answer>"
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
            answer_end_tag="</answer>"
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
            answer_end_tag="</answer>"
        )
        
class Phi3_PromptTemplate:
    def __init__(self):
        self.base_template = """{system_start}You are a clever chatbot specialized in answerings Maths, logic and reasoning questions.
        Stick to the question and provide only the answer and no more. I dont need explanations, neither intermediary steps.
        Let's think step by step.
        Intructions to solve the problem:
        {reasoning}
        Output:
        The format of the output should be:
        {solution}
        {system_ends}{start_user}{question}{end_user}{assistant_tag}

"""


    def generate_reasoning_prompt(self, question):
        """Generate a prompt for solving reasoning problems"""
        return self.base_template.format(
            question=question,
            system_start="<|system|>",
            system_ends="<|end|>",
            reasoning="""1. Analyze the question and identify the reasoning process
2. Break down the reasoning components
3. Apply relevant reasoning rules
4. Calculate step by step
5. Verify the result""",
            start_user="<|user|>",
            end_user="<|end|>",
            solution="[the solution will be provided here]",
            assistant_tag="<|assistant|>"
        )
        
        
class LLama_PromptTemplate:
    def __init__(self, nomenclature, examples):
        self.nomenclature = nomenclature
        self.examples= examples
        self.base_template_with_examples = """{begin_text}{start_header_id}system{end_header_id}You are a clever classifier assessing to which category each Event Visitor belong to,
        out of the 5 categories in section CATEGORIES. The format of each category is Category = Description of this category.
        You will be provided with an example of profile of each category on the section EXAMPLES. The format of each example is Category = Profile of this category.
        CATEGORIES
        ----------
        {categories}
        ------------
        EXAMPLES
        --------
        {examples}
        ----------
        Intructions to classify the Profile:
        {reasoning}
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
        return "\n".join([f"{key} = {value}\n" for key, value in self.nomenclature.items()])

    def generate_examples(self):
        return "\n".join([f"{key} = {value}\n" for key, value in self.examples.items()])

    def generate_keys(self):
        return list(self.examples.keys())

    def generate_clustering_prompt(self, profile, include_examples:bool =True):
        """Generate a prompt for getting Visitor Classification"""
        if include_examples:
            return self.base_template_with_examples.format(
            profile= profile,
            begin_text= "<|begin_of_text|>",
            start_header_id ="<|start_header_id|>",
            end_header_id="<|end_header_id|>",
            categories= self.generate_nomemclature(),
            examples = self.generate_examples(),
            reasoning=f"""1. Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        2. JobTitle, Job Level , Size of the company, Number of Employees, Number of Days in Hotel, can give you an Idea of how much interest has the visitor to come to the Event
                        3. Select 1 of the 5 choices in this list {self.generate_keys()} for each profile provided. Provide a confidence score based in 1 of this 3 classes. "High Confidence", "Mid-Level Confidence" and  "Low Confidence".
                        4. Based in your Choice in step 3, return an allocation to all of the 5 classes sorted from the most likely (the one you choose in step 3) to the less likely in a dictionary,
                         the dictionary will contain a key per class = key : class description, where key is the position on the rank and class description is one among the list {self.generate_keys()}
                        5. Return a json with the class for this profile, the confidence score and the sorted classes in a list. No preamble or explanation, or additional comments.
                        
                        THIS IS AN EXAMPLE OF, no what you has to return every time:
                        {{"searching_info_on_products_and_vendors" : "High Confidence", 
                                    "top_k": {{1:"searching_info_on_products_and_vendors',
                                            2:'Networking',
                                            3:'Learning',
                                            4:'early_purchasing_intention',
                                            5:'high_purchasing_intention'}}}}.
                        6. Only return the Json. Very Important. No additional Preamble, explanation or comments.
                        """,
            eot_id="<|eot_id|>",

        )
        else:
            return self.base_template_without_examples.format(
            profile= profile,
            begin_text= "<|begin_of_text|>",
            start_header_id ="<|start_header_id|>",
            end_header_id="<|end_header_id|>",
            categories= self.generate_nomemclature(),
            reasoning=f"""1. Key Questions (What best describes your reason for attending and Decision making power) and their answers have more weight than other questions.
                        2. JobTitle, Job Level , Size of the company, Number of Employees, Number of Days in Hotel, can give you an Idea of how much interest has the visitor to come to the Event
                        3. Select 1 of the 5 choices in this list {self.generate_keys()} for each profile provided. Provide a confidence score based in 1 of this 3 classes. "High Confidence", "Mid-Level Confidence" and  "Low Confidence".
                        4. Based in your Choice in step 3, return an allocation to all of the 5 classes sorted from the most likely (the one you choose in step 3) to the less likely in a dictionary,
                         the dictionary will contain a key per class = key : class description, where key is the position on the rank and class description is one among the list {self.generate_keys()}
                        5. Return a json with the class for this profile, the confidence score and the sorted classes in a list. No preamble or explanation, or additional comments.
                        
                        THIS IS AN EXAMPLE OF, no what you has to return every time:
                        {{"searching_info_on_products_and_vendors" : "High Confidence", 
                                    "top_k": {{1:"searching_info_on_products_and_vendors',
                                            2:'Networking',
                                            3:'Learning',
                                            4:'early_purchasing_intention',
                                            5:'high_purchasing_intention'}}}}.
                        6. Only return the Json. Very Important. No additional Preamble, explanation or comments.
                        """,
            eot_id="<|eot_id|>",

        )