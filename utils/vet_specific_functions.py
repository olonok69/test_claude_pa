"""
Veterinary-specific processing functions.
This module contains functions that are specific to veterinary events.
"""

def apply_vet_specific_practice_filling(processor, df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva, practices):
    """
    Apply veterinary-specific practice type filling logic.
    
    Args:
        processor: The RegistrationProcessor instance
        df_reg_demo_this: Current year combined dataframe
        df_reg_demo_last_bva: Last year main event dataframe
        df_reg_demo_last_lva: Last year secondary event dataframe
        practices: Practices reference dataframe
    
    Returns:
        Tuple of (df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva)
    """
    # Veterinary-specific column names (hardcoded for exact compatibility)
    this_year_col = "what_type_does_your_practice_specialise_in"
    past_year_col = "what_areas_do_you_specialise_in"

    # Fill missing practice types using vet-specific columns
    df_reg_demo_this = processor.fill_missing_practice_types(
        df_reg_demo_this, practices, column=this_year_col
    )
    df_reg_demo_last_bva = processor.fill_missing_practice_types(
        df_reg_demo_last_bva, practices, column=past_year_col
    )
    df_reg_demo_last_lva = processor.fill_missing_practice_types(
        df_reg_demo_last_lva, practices, column=past_year_col
    )
    
    return df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva


def apply_vet_specific_job_roles(processor, df):
    """
    Apply veterinary-specific job role processing logic.
    This uses the exact same logic as the original processor for perfect compatibility.
    
    Args:
        processor: The RegistrationProcessor instance
        df: DataFrame containing job role information
    
    Returns:
        DataFrame with processed job roles
    """
    import re
    from difflib import SequenceMatcher
    
    # Make a copy to avoid modifying the original dataframe
    df_copy = df.copy()

    # Use exact same potential roles and logic as original processor
    potential_roles = [
        "Student",
        "Other (please specify)",
        "Receptionist",
        "Head Nurse/Senior Nurse",
        "Vet/Vet Surgeon",
        "Practice Partner/Owner",
        "Academic",
        "Clinical or other Director",
        "Assistant Vet",
        "Vet/Owner",
        "Vet Nurse",
        "Locum Vet",
        "Practice Manager",
        "Locum RVN",
    ]

    # Only process rows where job_role is "NA"
    mask = df_copy["job_role"] == "NA"

    # Apply each rule in sequence (exact same as original)
    for idx in df_copy[mask].index:
        job_title = str(df_copy.loc[idx, "JobTitle"]).lower()

        # Rule 1-6: Check for specific strings in JobTitle (exact same as original)
        if "surgeon" in job_title:
            df_copy.loc[idx, "job_role"] = "Vet/Vet Surgeon"
        elif "nurse" in job_title:
            df_copy.loc[idx, "job_role"] = "Vet Nurse"
        elif "rvn" in job_title:
            df_copy.loc[idx, "job_role"] = "Vet Nurse"
        elif "locum" in job_title:
            df_copy.loc[idx, "job_role"] = "Locum Vet"
        elif "student" in job_title:
            df_copy.loc[idx, "job_role"] = "Student"
        elif "assistant" in job_title:
            df_copy.loc[idx, "job_role"] = "Assistant Vet"
        else:
            # Rule 7: Use text similarity to find the best matching role

            # Clean the job title: remove common words that might interfere with matching
            cleaned_title = re.sub(r"\b(and|the|of|in|at|for)\b", "", job_title)

            # Find the role with highest similarity score
            best_match = None
            best_score = 0

            for role in potential_roles:
                # Calculate similarity between job title and each potential role
                role_lower = role.lower()

                # Check for key terms in the role
                role_terms = role_lower.split("/")
                role_terms.extend(role_lower.split())

                # Calculate max similarity with any term in the role
                max_term_score = 0
                for term in role_terms:
                    if len(term) > 2:  # Only consider meaningful terms
                        if term in cleaned_title:
                            term_score = 0.9  # High score for direct matches
                        else:
                            # Use sequence matcher for fuzzy matching
                            term_score = SequenceMatcher(
                                None, cleaned_title, term
                            ).ratio()
                        max_term_score = max(max_term_score, term_score)

                if max_term_score > best_score:
                    best_score = max_term_score
                    best_match = role

            # If similarity is above threshold, use the best match
            if best_score > 0.3:  # Use exact same threshold as original
                df_copy.loc[idx, "job_role"] = best_match
            else:
                # Default to "Other" if no good match
                df_copy.loc[idx, "job_role"] = "Other (please specify)"

    # Final rule: Replace any occurrence of "Other" with "Other (please specify)"
    other_mask = df_copy["job_role"].str.contains(
        "Other", case=False, na=False
    ) & ~df_copy["job_role"].eq("Other (please specify)")
    df_copy.loc[other_mask, "job_role"] = "Other (please specify)"

    processor.logger.info(f"Processed job roles for {mask.sum()} records using vet-specific logic")
    return df_copy


def add_vet_specific_methods(processor):
    """
    Add veterinary-specific methods to the processor instance.
    
    Args:
        processor: The RegistrationProcessor instance to enhance
    """
    # Add the vet-specific practice filling method
    processor.apply_vet_specific_practice_filling = lambda *args: apply_vet_specific_practice_filling(processor, *args)
    
    # Override the job role processing method
    processor.process_job_roles = lambda df: apply_vet_specific_job_roles(processor, df)