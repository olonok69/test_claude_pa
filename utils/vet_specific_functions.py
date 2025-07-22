"""
Veterinary-specific processing functions - Version 5.
This module contains functions that are specific to veterinary events.
Ensures robust method binding and exact compatibility with original processor.
"""

import logging

def apply_vet_specific_practice_filling(self, df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva, practices):
    """
    Apply veterinary-specific practice type filling logic.
    
    Args:
        self: The RegistrationProcessor instance
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
    df_reg_demo_this = self.fill_missing_practice_types(
        df_reg_demo_this, practices, column=this_year_col
    )
    df_reg_demo_last_bva = self.fill_missing_practice_types(
        df_reg_demo_last_bva, practices, column=past_year_col
    )
    df_reg_demo_last_lva = self.fill_missing_practice_types(
        df_reg_demo_last_lva, practices, column=past_year_col
    )
    
    return df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva


def apply_vet_specific_job_roles(self, df):
    """
    Apply veterinary-specific job role processing logic.
    This is EXACTLY the same logic as the original processor - copied line by line.
    
    Args:
        self: The RegistrationProcessor instance
        df: DataFrame containing job role information
    
    Returns:
        DataFrame with processed job roles
    """
    import re
    from difflib import SequenceMatcher
    
    # Make a copy to avoid modifying the original dataframe
    df_copy = df.copy()

    # Define potential roles - EXACTLY as in original processor
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

    # Apply each rule in sequence - EXACTLY as in original processor
    for idx in df_copy[mask].index:
        job_title = str(df_copy.loc[idx, "JobTitle"]).lower()

        # Rule 1-6: Check for specific strings in JobTitle - EXACTLY as original
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
            # Rule 7: Use text similarity - EXACTLY as original

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
            if best_score > 0.3:  # Adjustable threshold - EXACTLY as original
                df_copy.loc[idx, "job_role"] = best_match
            else:
                # Default to "Other" if no good match
                df_copy.loc[idx, "job_role"] = "Other (please specify)"

    # Final rule: Replace any occurrence of "Other" with "Other (please specify)" - EXACTLY as original
    other_mask = df_copy["job_role"].str.contains(
        "Other", case=False, na=False
    ) & ~df_copy["job_role"].eq("Other (please specify)")
    df_copy.loc[other_mask, "job_role"] = "Other (please specify)"

    self.logger.info(f"Processed job roles for {mask.sum()} records using vet-specific logic")
    return df_copy


def add_vet_specific_methods(processor):
    """
    Add veterinary-specific methods to the processor instance.
    Version 5: More robust method binding with extensive logging.
    
    Args:
        processor: The RegistrationProcessor instance to enhance
    """
    import types
    
    # Add extensive logging to understand what's happening
    logger = logging.getLogger(__name__)
    logger.info("=== STARTING VET-SPECIFIC FUNCTION APPLICATION ===")
    logger.info(f"Processor type: {type(processor)}")
    logger.info(f"Processor has process_job_roles: {hasattr(processor, 'process_job_roles')}")
    
    try:
        # Store the original methods
        if hasattr(processor, 'process_job_roles'):
            processor._original_process_job_roles = processor.process_job_roles
            logger.info("Stored original process_job_roles method")
        
        if hasattr(processor, 'fill_event_specific_practice_types'):
            processor._original_fill_event_specific_practice_types = processor.fill_event_specific_practice_types
            logger.info("Stored original fill_event_specific_practice_types method")
        
        # Add the vet-specific practice filling method
        processor.apply_vet_specific_practice_filling = types.MethodType(
            apply_vet_specific_practice_filling, processor
        )
        logger.info("Added apply_vet_specific_practice_filling method")
        
        # Override the job role processing method with the exact vet-specific logic
        processor.process_job_roles = types.MethodType(
            apply_vet_specific_job_roles, processor
        )
        logger.info("Overrode process_job_roles method with vet-specific logic")
        
        # Override the practice filling method to use vet-specific logic
        def vet_fill_event_specific_practice_types(self, df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva, practices):
            return self.apply_vet_specific_practice_filling(df_reg_demo_this, df_reg_demo_last_bva, df_reg_demo_last_lva, practices)
        
        processor.fill_event_specific_practice_types = types.MethodType(
            vet_fill_event_specific_practice_types, processor
        )
        logger.info("Overrode fill_event_specific_practice_types method")
        
        # Add a flag to indicate vet-specific functions are active
        processor._vet_specific_active = True
        
        # Log success with a message that will be visible in the test output
        success_msg = "*** VET-SPECIFIC FUNCTIONS SUCCESSFULLY APPLIED ***"
        logger.info(success_msg)
        processor.logger.info(success_msg)
        
        logger.info("=== VET-SPECIFIC FUNCTION APPLICATION COMPLETED ===")
        
    except Exception as e:
        error_msg = f"*** ERROR APPLYING VET-SPECIFIC FUNCTIONS: {e} ***"
        logger.error(error_msg, exc_info=True)
        processor.logger.error(error_msg)
        raise


def verify_vet_functions_applied(processor):
    """
    Verify that vet-specific functions have been applied correctly.
    
    Args:
        processor: The RegistrationProcessor instance to check
        
    Returns:
        bool: True if vet-specific functions are active
    """
    logger = logging.getLogger(__name__)
    
    checks = [
        hasattr(processor, '_vet_specific_active'),
        hasattr(processor, 'apply_vet_specific_practice_filling'),
        hasattr(processor, '_original_process_job_roles'),
    ]
    
    all_passed = all(checks)
    logger.info(f"Vet-specific function verification: {all_passed}")
    logger.info(f"Individual checks: {checks}")
    
    return all_passed