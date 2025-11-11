def check_eligibility(physics, chemistry, math, category):
    """
    Check if a student is eligible for admission based on PCM marks and category.
    """

    # Calculate PCM percentage
    total_marks = physics + chemistry + math
    pcm_percentage = (total_marks / 300) * 100  

    # Define minimum eligibility
    min_percentage = 45 if category.lower() == "open" else 40

    # Eligibility decision
    if pcm_percentage >= min_percentage:
        return True, f"Eligible! Your PCM percentage is {pcm_percentage:.2f}%."
    else:
        return False, f"Not eligible. Your PCM percentage is {pcm_percentage:.2f}%, which is below the required {min_percentage}%."