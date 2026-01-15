# Role-Based AI: Course Recommendation System - Mini practical example

def recommend_course(student_interests):
    """
    Recommend a course based on student's interests using rule-based AI
    """
    if 'Math' in student_interests:
        return 'Python'
    elif 'Biology' in student_interests:
        return 'Biotechnology'
    elif 'Writing' in student_interests:
        return 'Content Creation'
    else:
        return 'General Studies'

# user input
print("=== Course Recommendation System ===")
print("Available interests: Math, Biology, Writing")
user_input = input("Enter your interest: ").strip().title()

# convert input to list
interests = [user_input]

# gives recommendation
recommendation = recommend_course(interests)


print(f"\nBased on your interest in '{user_input}', we recommend: {recommendation}")