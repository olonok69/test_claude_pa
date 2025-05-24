from typing import List
import pandas as pd
from presidio_analyzer import (
    PatternRecognizer,
    EntityRecognizer,
    RecognizerResult,
)
import tekswift
from presidio_analyzer.nlp_engine import NlpArtifacts
from presidio_analyzer.predefined_recognizers.aba_routing_recognizer import (
    AbaRoutingRecognizer,
)
import re
from collections import OrderedDict
from json import JSONDecoder
import os
import logging

ROOT = os.path.dirname(__file__)

# Define EN new recognizers
titles_list = [
    "Sir",
    "Ma'am",
    "Madam",
    "Mr.",
    "Mrs.",
    "Ms.",
    "Miss",
    "Dr.",
    "Professor",
    "sir",
    "ma'am",
    "madam",
    "mr.",
    "mrs.",
    "ms.",
    "miss",
    "dr.",
    "professor",
]
# Gender Preliminary list
gender = [
    "agender",
    "transgender",
    "nonbinary",
    "cisgender",
    "genderfluid",
    "genderqueer",
    "bigender",
    "ftm",
    "nonconforming-gender",
    "man",
    "intersex",
    "woman",
    "two-spirit",
    "androgyne",
    "androgynous",
    "omnigender",
    "transwoman",
    "transmen",
    "female",
    "male",
]

# Sexual Orientations preliminary list
sexual_orientation = ["gay", "lesbian", "straight", "bisexual", "asexual"]


class SWIFTRecognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect SWIFT CODES. Use app Tekswift
    """

    expected_confidence_level = 0.7  # expected confidence level for this recognizer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokens which represent SWIFT/BIC CODES.
        """
        results = []

        # iterate over the spaCy tokens, and call `token.like_num`
        for token in nlp_artifacts.tokens:
            # ONLY tokens longer than 7 chars typically 8 to 11 chars
            if len(token.text.upper()) in [8, 9, 10, 11]:
                try:
                    swift = tekswift.lookup_swiftcode(token.text.upper())
                    if swift != None:

                        if set(swift.keys()) == {"branch", "city", "institution"}:
                            result = RecognizerResult(
                                entity_type="SWIFT_CODE",
                                start=token.idx,
                                end=token.idx + len(token),
                                score=self.expected_confidence_level,
                            )
                            results.append(result)
                    else:
                        logging.info(
                            f"tekswift package did not return anything {token.text.upper()}"
                        )
                        continue
                except Exception:
                    # exception produced by tokens which are not swiftcodes
                    continue
            else:
                continue
        return results


class Social_Network_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect Social Network Links
    """

    expected_confidence_level = 0.7  # expected confidence level for this recognizer
    regexes = []
    regex_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load(self) -> None:
        """No loading is required."""

        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyze if there is social Network profile
        """
        regexes = []
        regex_list = []
        results = []
        with open(os.path.join(ROOT, "data", "regexes.json")) as data_file:
            # ensure json/dict order is consistent below python 3.6
            # -> testing for correct readme won't fail
            customdecoder = JSONDecoder(object_pairs_hook=OrderedDict)
            regexes = customdecoder.decode(data_file.read())
            # Get all possible Social Network Regex
            for k1 in regexes.keys():
                for k2 in regexes[k1].keys():
                    regex_list.append(regexes[k1][k2].get("regex"))
        # iterate over the spaCy tokens, and call `token.like_num`
        for token in nlp_artifacts.tokens:
            if len(token) >= 6:
                for regex in regex_list:
                    matcher = re.compile(regex)
                    match = matcher.search(token.text)
                    if match:
                        result = RecognizerResult(
                            entity_type="SOCIAL_NETWORK_PROFILE",
                            start=token.idx,
                            end=token.idx + len(token),
                            score=self.expected_confidence_level,
                        )
                        results.append(result)

        return results


class AgeRecognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect AGE
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokens which represent numbers (either 123 or One Two Three).
        """
        results = []

        # iterate over the spaCy tokens, and call `token.like_num`
        p = re.compile("\s+\d{1,3}\s*(years){1}", re.IGNORECASE)
        for x in p.finditer(text):
            match = x.group(0)
            match = match.lower()
            txt = match.replace("years", "")
            txt = txt.strip()
            if int(txt) < 125:
                lemmas = []
                tokens = []
                for token in nlp_artifacts.tokens:
                    lemmas.append(token.lemma_)
                    tokens.append(token.text)
                # check with lemma of verb be if we are build a sentence like I have 90 years
                # or she has 30 years

                if lemmas[tokens.index(txt) - 1] in ["be", "have"]:
                    result = RecognizerResult(
                        entity_type="AGE",
                        start=x.span()[0] + 1,
                        end=x.span()[1],
                        score=self.expected_confidence_level,
                    )
                # case the word age appears before 1 or 2 position witx n years
                elif (
                    tokens[tokens.index(txt) - 1].lower() == "age"
                    or tokens[tokens.index(txt) - 2].lower() == "age"
                ):
                    result = RecognizerResult(
                        entity_type="AGE",
                        start=x.span()[0] + 1,
                        end=x.span()[1],
                        score=0.9,
                    )
                else:
                    result = RecognizerResult(
                        entity_type="AGE",
                        start=x.span()[0] + 1,
                        end=x.span()[1],
                        score=0.5,
                    )
                results.append(result)

        return results


class SO_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect Sexual Orientation according to list of Ocurrences
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokens which represent numbers (either 123 or One Two Three).
        """
        n_sex_orientation = []
        for g in sexual_orientation:
            n_sex_orientation.append(g.lower())

        results = []

        # iterate over the spaCy tokens, and call `token.like_num`
        lemmas = []
        tokens = []
        indices = []
        for token in nlp_artifacts.tokens:
            lemmas.append(token.lemma_.lower())
            tokens.append(token.text.lower())
            indices.append(token.idx)

        for i, token in zip(indices, tokens):

            # check with lemma of verb be if we are build a sentence like I have 90 years
            # or she has 30 years
            if (
                lemmas[tokens.index(token) - 1] in ["be", "have", "as"]
                and token in n_sex_orientation
            ):

                result = RecognizerResult(
                    entity_type="SEXUAL_PREFERENCE",
                    start=i,
                    end=i + len(token),
                    score=self.expected_confidence_level,
                )
                results.append(result)
            elif token in n_sex_orientation:
                if token.lower() == "straight":

                    result = RecognizerResult(
                        entity_type="SEXUAL_PREFERENCE",
                        start=i,
                        end=i + len(token),
                        score=0.1,
                    )
                    results.append(result)

                else:

                    result = RecognizerResult(
                        entity_type="SEXUAL_PREFERENCE",
                        start=i,
                        end=i + len(token),
                        score=0.5,
                    )
                    results.append(result)
            else:
                continue

        return results


class GENDER_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect Gender according to list of Ocurrences
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokens which represent numbers (either 123 or One Two Three).
        """
        n_gender = []
        for g in gender:
            n_gender.append(g.lower())

        results = []
        lemmas = []
        tokens = []
        indices = []
        for token in nlp_artifacts.tokens:
            lemmas.append(token.lemma_.lower())
            tokens.append(token.text.lower())
            indices.append(token.idx)

        for i, token in zip(indices, tokens):
            try:
                # iterate trough the list of indices, tokens and lemmas
                if i > 0 and token.lower() in n_gender:
                    # if token in gender list and lemma previous token in list "be","have", "as", "from", "to"
                    if lemmas[tokens.index(token.lower()) - 1] in [
                        "be",
                        "have",
                        "as",
                        "from",
                        "to",
                    ]:

                        result = RecognizerResult(
                            entity_type="GENDER",
                            start=i,
                            end=i + len(token.strip()),
                            score=self.expected_confidence_level,
                        )
                        results.append(result)
                    else:
                        # if token in gender list but lemma previous token not in list "be","have", "as", "from", "to"
                        result = RecognizerResult(
                            entity_type="GENDER",
                            start=i,
                            end=i + len(token.strip()),
                            score=0.75,
                        )
                        results.append(result)
                # case first token
                elif i == 0 and token.lower() in n_gender:
                    result = RecognizerResult(
                        entity_type="GENDER",
                        start=i,
                        end=i + len(token.strip()),
                        score=0.75,
                    )
                    results.append(result)

            except Exception as e:
                logging.warning(f"Exception {e} in token: {token} indice: {i}")
                continue

        return results


# Occupations Recognizer

occupation = pd.read_csv(os.path.join(ROOT, "data", "occupations.csv"))
occupation["Occupations"] = occupation.Occupations.str.lower()
occupation_list = occupation.Occupations.to_list()

# JOB TITLE RECOGNIZER
jobs = pd.read_csv(os.path.join(ROOT, "data", "job_list.csv"))
jobs["job_title"] = jobs.job_title.str.lower()
jobs_list = jobs.job_title.to_list()

# races
races = pd.read_csv(os.path.join(ROOT, "data", "races.csv"))
races["race"] = races.race.str.lower()
races_list = races.race.to_list()

# marital status recognizer


class Maritial_Status_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect Marital Status  according to list of Ocurrences
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer
    regexes = []
    regex_list = []

    def load(self) -> None:
        """No loading is required."""

        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyze if there is a marital estatus pii entity
        """

        results = []
        lemmas = []
        tokens = []
        indices = []
        for token in nlp_artifacts.tokens:
            lemmas.append(token.lemma_.lower())
            tokens.append(token.text.lower())
            indices.append(token.idx)
        # races
        marital = pd.read_csv(os.path.join(ROOT, "data", "marital_status.csv"))
        marital["status"] = marital.status.str.lower()
        marital_list = marital.status.to_list()
        for i, token in zip(indices, tokens):
            if token.lower() in marital_list:
                # If token lemma before is "be", "have", "in" we get the max score
                if lemmas[tokens.index(token.lower()) - 1] in ["be", "have", "in"]:

                    result = RecognizerResult(
                        entity_type="MARITAL_STATUS",
                        start=i,
                        end=i + len(token),
                        score=self.expected_confidence_level,
                    )
                    results.append(result)

                # If token lemma before not is "be", "have", "in" and text is single we get the min score
                elif (
                    lemmas[tokens.index(token.lower()) - 1] not in ["be", "have", "in"]
                ) and (token.lower() == "single"):

                    result = RecognizerResult(
                        entity_type="MARITAL_STATUS",
                        start=i,
                        end=i + len(token),
                        score=0.1,
                    )
                    results.append(result)

                # If token lemma before is not in  "be", "have", "in" and text is not single  we get .5
                else:

                    result = RecognizerResult(
                        entity_type="MARITAL_STATUS",
                        start=i,
                        end=i + len(token),
                        score=0.5,
                    )
                    results.append(result)

        return results


class ABA_Routing_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect ABA Routing Numbers according to list of Ocurrences
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer
    regexes = []
    regex_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load(self) -> None:
        """No loading is required."""

        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyze if there is a marital estatus pii entity
        """

        results = []

        aba = pd.read_csv(os.path.join(ROOT, "data", "aba.csv"))
        aba["ABA"] = aba["ABA"].astype("str").str.zfill(9)
        aba_list = aba.ABA.to_list()
        logging.info(f"Length ABA list {len(aba_list)}")

        for token in nlp_artifacts.tokens:

            if token.text.lower() in aba_list:

                start = text.lower().find(token.text.lower())
                result = RecognizerResult(
                    entity_type="ABA_ROUTING_NUMBER",
                    start=start,
                    end=start + len(token.text),
                    score=self.expected_confidence_level,
                )
                results.append(result)
                logging.info(f"detected ABA routing Number {token.text.lower()}")

        return results


# weight pattern
class Weigth_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect Weigth according to Pattern and context
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokes which can be a weigth PII entity
        """
        results = []

        # iterate over the spaCy tokens, and call `token.like_num`
        p = re.compile(
            "\s+\d{1,3}\.{0,1}\d{0,3}\s*(kg|kilogram|gram|lb|pounds){1}\s*\,*"
        )
        for x in p.finditer(text):
            match = x.group(0)
            threshold = 0
            if "kg" in match.lower():
                threshold = 300  # kgs
                txt = match.replace("kg", "")
            elif "kilogram" in match.lower():
                threshold = 300  # kgs
                txt = match.replace("kilogram", "")
            elif "lb" in match.lower():
                threshold = 500  # pounds
                txt = match.replace("lb", "")
            elif "pounds" in match.lower():
                threshold = 500  # pounds
                txt = match.replace("pounds", "")
            elif "gram" in match.lower():
                threshold = 300000  # pounds
                txt = match.replace("gram", "")
                txt = txt.replace(" s ", "")

            txt = txt.replace(",", "")
            txt = txt.strip()
            if float(txt) < threshold:
                lemmas = []
                tokens = []
                for token in nlp_artifacts.tokens:
                    lemmas.append(token.lemma_)
                    tokens.append(token.text)
                # check with lemma of verb be if we are build a sentence like I have 90 years
                # or she has 30 years
                try:
                    if lemmas[tokens.index(txt) - 1] in ["be", "have", "of"]:
                        match1 = match.replace(",", "")
                        match1 = match1.strip()
                        start = text.lower().find(match1.lower())
                        result = RecognizerResult(
                            entity_type="WEIGHT",
                            start=start,
                            end=start + len(match1),
                            score=self.expected_confidence_level,
                        )
                    else:
                        match1 = match.replace(",", "")
                        match1 = match1.strip()
                        start = text.lower().find(match1.lower())
                        result = RecognizerResult(
                            entity_type="WEIGHT",
                            start=start,
                            end=start + len(match1),
                            score=0.5,
                        )
                    results.append(result)
                except Exception as e:
                    logging.warning(
                        f"Exception in Recognizer Weight: {e}  match {match1}"
                    )
                    continue

        return results


# heigth pattern
class Heigth_Recognizer(EntityRecognizer):
    """
    EntityRecognizer Custom to detect heigth according to Pattern and context
    """

    expected_confidence_level = 1.0  # expected confidence level for this recognizer

    def load(self) -> None:
        """No loading is required."""
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """
        Analyzes test to find tokes which can be a weigth PII entity
        """
        results = []

        # iterate over the spaCy tokens, and call `token.like_num`
        p = re.compile(
            "\s+\d{1,3}\.{0,1}\d{0,3}\s*(cm|m|meter|centimeter|in|inch|inches)\s*\,*"
        )
        for x in p.finditer(text):
            match = x.group(0)
            threshold = 0
            if "cm" in match.lower():
                threshold = 2500  # cm
                txt = match.replace("cm", "")
            elif "centimeter" in match.lower():
                threshold = 2500  # cm
                txt = match.replace("centimeter", "")
            elif "m" in match.lower():
                threshold = 2.6  # meters
                txt = match.replace("m", "")
            elif "meter" in match.lower():
                threshold = 2.6  # pounds
                txt = match.replace("meter", "")
                txt = txt.replace(" s ", "")
            elif "in" in match.lower():
                threshold = 1000  # meters
                txt = match.replace("in", "")
            elif "inch" in match.lower():
                threshold = 1000  # inches
                txt = match.replace("inch", "")
                txt = txt.replace(" es ", "")

            txt = txt.replace(",", "")
            txt = txt.strip()
            if float(txt) < threshold:
                lemmas = []
                tokens = []
                for token in nlp_artifacts.tokens:
                    lemmas.append(token.lemma_)
                    tokens.append(token.text)
                # check with lemma of verb be if we are build a sentence like I have 90 years
                # or she has 30 years
                try:
                    if lemmas[tokens.index(txt) - 1] in ["be", "have", "of"]:
                        match1 = match.replace(",", "")
                        match1 = match1.strip()
                        start = text.lower().find(match1.lower())
                        result = RecognizerResult(
                            entity_type="HEIGHT",
                            start=start,
                            end=start + len(match1),
                            score=self.expected_confidence_level,
                        )
                    else:
                        match1 = match.replace(",", "")
                        match1 = match1.strip()
                        start = text.lower().find(match1.lower())
                        result = RecognizerResult(
                            entity_type="HEIGHT",
                            start=start,
                            end=start + len(match1),
                            score=0.5,
                        )
                    results.append(result)
                except Exception as e:
                    logging.warning(
                        f"Error Recognizer Height. Exception {e} match {match1}"
                    )
                    continue
        return results


# Create pattern recognizers
titles_recognizer = PatternRecognizer(
    supported_entity="TITLE_EN",
    deny_list=titles_list,
    supported_language="en",
)
# OCCUPATION
occupation_recognizer = PatternRecognizer(
    supported_entity="OCCUPATION",
    deny_list=occupation_list,
    supported_language="en",
    context=["job", "occupation"],
)
# JOB TITLE
jobs_recognizer = PatternRecognizer(
    supported_entity="JOB_TITLE",
    deny_list=jobs_list,
    supported_language="en",
    context=["job", "title"],
)
# RACE/ETNICITY
race_recognizer = PatternRecognizer(
    supported_entity="RACE",
    deny_list=races_list,
    supported_language="en",
    context=["race", "ethnicity"],
)


# ABA ROUTING NUMBER
aba_recognizer = AbaRoutingRecognizer(
    supported_language="en",
)
# SWIFT recognizer
swift_recognizer = SWIFTRecognizer(
    supported_entities=["SWIFT_CODE"], supported_language="en"
)
# SOCIAL NETWORK PROFILE recognizer
snp_recognizer = Social_Network_Recognizer(
    supported_entities=["SOCIAL_NETWORK_PROFILE"], supported_language="en"
)
# AGE RECOGNIZER
age_recognizer = AgeRecognizer(supported_entities=["AGE"])
# Sexual Orientation Recognizer
sex_orientation_recognizer = SO_Recognizer(supported_entities=["SEXUAL_PREFERENCE"])
# GENDER RECOGNIZER
gender_recognizer = GENDER_Recognizer(supported_entities=["GENDER"])
# MARITAL_STATUS
marital_recognizer = Maritial_Status_Recognizer(supported_entities=["MARITAL_STATUS"])

# Weight Recognizer
weight_recognizer = Weigth_Recognizer(supported_entities=["WEIGHT"])
# Height Recognizer
height_recognizer = Heigth_Recognizer(supported_entities=["HEIGHT"])
