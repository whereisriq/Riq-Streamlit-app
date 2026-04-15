# create_student_csv.py
import csv
import random

print("="*60)
print("CREATING SAMPLE STUDENT DATA CSV")
print("="*60)

# Sample student names
first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason", 
               "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
               "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Abigail", "Michael",
               "Emily", "Daniel", "Elizabeth", "Matthew", "Sofia", "David", "Avery", "Joseph"]

last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
              "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", 
              "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

# Generate 30 students
students = []

for i in range(30):
    student = {
        'Student_ID': f'STU{2024001 + i}',
        'Name': f'{random.choice(first_names)} {random.choice(last_names)}',
        'Math': random.randint(45, 98),
        'English': random.randint(50, 95),
        'Science': random.randint(48, 96),
        'History': random.randint(52, 94),
        'Geography': random.randint(55, 92)
    }
    students.append(student)

# Create some patterns for realistic data
# Make some students consistently strong
for i in [0, 5, 10]:
    students[i]['Math'] = random.randint(85, 98)
    students[i]['English'] = random.randint(85, 95)
    students[i]['Science'] = random.randint(88, 96)
    students[i]['History'] = random.randint(85, 94)
    students[i]['Geography'] = random.randint(82, 92)

# Make some students struggle
for i in [2, 7, 12]:
    students[i]['Math'] = random.randint(45, 60)
    students[i]['English'] = random.randint(50, 62)
    students[i]['Science'] = random.randint(48, 58)
    students[i]['History'] = random.randint(52, 64)
    students[i]['Geography'] = random.randint(55, 65)

# Make Math generally harder (lower scores)
for student in students:
    if student['Math'] > 70:
        student['Math'] -= random.randint(5, 15)

# Save to CSV
filename = 'student_results.csv'
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Student_ID', 'Name', 'Math', 'English', 
                                           'Science', 'History', 'Geography'])
    writer.writeheader()
    writer.writerows(students)

print(f"\n✅ Created {filename}")
print(f"📊 Generated {len(students)} student records")
print(f"📚 Subjects: Math, English, Science, History, Geography")

# Print summary statistics
print("\n" + "="*60)
print("QUICK PREVIEW")
print("="*60)

subjects = ['Math', 'English', 'Science', 'History', 'Geography']
print("\nAverage Scores:")
for subject in subjects:
    avg = sum(s[subject] for s in students) / len(students)
    print(f"  {subject}: {avg:.1f}")

print(f"\nFirst 5 students:")
print("-"*60)
for i, student in enumerate(students[:5], 1):
    print(f"{i}. {student['Name']} (ID: {student['Student_ID']})")
    print(f"   Math: {student['Math']}, English: {student['English']}, "
          f"Science: {student['Science']}, History: {student['History']}, "
          f"Geography: {student['Geography']}")

print("\n" + "="*60)
print("✅ SAMPLE DATA CREATED SUCCESSFULLY!")
print("="*60)
print("\nNow you can run:")
print(f"  python student_analyzer.py {filename}")
print(f"  python student_analyzer.py {filename} --output analysis_report.txt")
print("="*60)