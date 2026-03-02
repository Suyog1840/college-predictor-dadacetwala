import simulation_engine as se

test_cases = [
    {
        "id": 1,
        "description": "High Scorer (OPEN Male, No Prefs)",
        "scores": {"MHTCET": 98.4, "JEE": 95.0},
        "category": "OPEN",
        "gender": "Male",
        "homeUniversity": "Mumbai University",
        "branchPreference": [],
        "districtPreference": []
    },
    {
        "id": 2,
        "description": "Mid-tier Female (OPEN, IT preferred)",
        "scores": {"MHTCET": 85.0},
        "category": "OPEN",
        "gender": "Female",
        "homeUniversity": "Savitribai Phule Pune University",
        "branchPreference": ["Information Technology"],
        "districtPreference": ["Pune"]
    },
    {
        "id": 3,
        "description": "OBC Male (Computer Engineering)",
        "scores": {"MHTCET": 90.5, "JEE": 82.3},
        "category": "OBC",
        "gender": "Male",
        "homeUniversity": "Shivaji University",
        "branchPreference": ["Computer Engineering"],
        "districtPreference": []
    },
    {
        "id": 4,
        "description": "SC Female (Core Branches)",
        "scores": {"MHTCET": 75.0},
        "category": "SC",
        "gender": "Female",
        "homeUniversity": "Dr. Babasaheb Ambedkar Marathwada University",
        "branchPreference": ["Mechanical Engineering", "Civil Engineering"],
        "districtPreference": ["Aurangabad", "Nashik"]
    },
    {
        "id": 5,
        "description": "ST Male (Low Score)",
        "scores": {"MHTCET": 55.4},
        "category": "ST",
        "gender": "Male",
        "homeUniversity": "Gondwana University",
        "branchPreference": [],
        "districtPreference": []
    },
    {
        "id": 6,
        "description": "NT2 Female (Specific District)",
        "scores": {"MHTCET": 89.2},
        "category": "NT2",
        "gender": "Female",
        "homeUniversity": "Savitribai Phule Pune University",
        "branchPreference": [],
        "districtPreference": ["Mumbai City", "Mumbai Suburban"]
    },
    {
        "id": 7,
        "description": "VJ Male (Artificial Intelligence)",
        "scores": {"MHTCET": 93.1, "JEE": 88.5},
        "category": "VJ",
        "gender": "Male",
        "homeUniversity": "Sant Gadge Baba Amravati University",
        "branchPreference": ["Artificial Intelligence and Data Science"],
        "districtPreference": []
    },
    {
        "id": 8,
        "description": "OPEN Female (AI Quota Focus - JEE Only)",
        "scores": {"JEE": 91.0},
        "category": "OPEN",
        "gender": "Female",
        "homeUniversity": "Mumbai University",
        "branchPreference": [],
        "districtPreference": []
    },
    {
        "id": 9,
        "description": "EWS Male (Electrical Engineer)",
        "scores": {"MHTCET": 80.0},
        "category": "EWS",
        "gender": "Male",
        "homeUniversity": "Punyashlok Ahilyadevi Holkar Solapur University",
        "branchPreference": ["Electrical Engineering"],
        "districtPreference": []
    },
    {
        "id": 10,
        "description": "NT1 Female (Biomed/Cheincal)",
        "scores": {"MHTCET": 78.4},
        "category": "NT1",
        "gender": "Female",
        "homeUniversity": "Rashtrasant Tukadoji Maharaj Nagpur University",
        "branchPreference": ["Chemical Engineering", "Biomedical Engineering"],
        "districtPreference": []
    },
    {
        "id": 11,
        "description": "TFWS Applicant (OPEN Male, Very High Score)",
        "scores": {"MHTCET": 99.5},
        "category": "OPEN",
        "gender": "Male",
        "homeUniversity": "Savitribai Phule Pune University",
        "branchPreference": ["Computer Engineering", "Information Technology"],
        "districtPreference": ["Pune", "Mumbai Suburban"]
    },
    {
        "id": 12,
        "description": "OBC Female (Very Low Score)",
        "scores": {"MHTCET": 35.0},
        "category": "OBC",
        "gender": "Female",
        "homeUniversity": "Kaviyitri Bahinabai Chaudhari North Maharashtra University",
        "branchPreference": [],
        "districtPreference": []
    },
    {
        "id": 13,
        "description": "SBC Male (Electronics preference)",
        "scores": {"MHTCET": 84.6},
        "category": "SBC",
        "gender": "Male",
        "homeUniversity": "Swami Ramanand Teerth Marathwada University",
        "branchPreference": ["Electronics and Telecommunication Engg", "Electronics Engineering"],
        "districtPreference": []
    },
    {
        "id": 14,
        "description": "OPEN Female (Non-MH University, AI only basically)",
        "scores": {"JEE": 92.4, "MHTCET": 81.0},
        "category": "OPEN",
        "gender": "Female",
        "homeUniversity": "Other University",
        "branchPreference": ["Computer Science and Engineering"],
        "districtPreference": ["Nagpur"]
    },
    {
        "id": 15,
        "description": "SEBC Male (Data Science / Cyber Security target)",
        "scores": {"MHTCET": 91.2},
        "category": "SEBC",
        "gender": "Male",
        "homeUniversity": "Shivaji University",
        "branchPreference": ["Computer Science and Engineering (Cyber Security)", "Data Science"],
        "districtPreference": []
    }
]

print("Starting verification test suite...\n")

for i, test in enumerate(test_cases):
    print(f"===========================================================")
    print(f"TEST {i+1}: {test['description']}")
    print(f"Scores: {test['scores']} | Category: {test['category']} | Gender: {test['gender']}")
    print(f"===========================================================")
    
    try:
        predictions = se.predict(test)
        
        print("-- Overall Top 5 Matches --")
        if not predictions:
            print("   [NO MATCHES FOUND]")
        for rank, r in enumerate(predictions):
            print(f"   {rank+1}. [{r['examType']}] {r['collegeName']} ({r['branchName']}) - Prob: {r['probability']}%")
        print("\n")
        
    except Exception as e:
        print(f"!!! ERROR RUNNING TEST {i+1}: {e} !!!")

print("Tests completed.")
