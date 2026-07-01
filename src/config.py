import os
from dotenv import load_dotenv

load_dotenv()

ZOTERO_LIBRARY_ID = os.getenv("ZOTERO_LIBRARY_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
ZOTERO_BASE_DIR = os.getenv("ZOTERO_BASE_DIR")

# Zotero uses unique IDs for collections, not names. 
# You will need to map your specific folder IDs here later.
# COLLECTION_IDS = {
#     "00 - Unclassified": "2R3JBEZL",
#     "01 - Digital Humans & Appearance": "3QD6UQHX",
#     "01 - Digital Humans & Appearance/Data-Driven": "RDH88XA7",
#     "01 - Digital Humans & Appearance/Hybrid": "GCSZPWXB",
#     "01 - Digital Humans & Appearance/Physics-Based": "NWWX4PGK",
#     "02 - Motion Synthesis & Animation": "ZHXNE99G",
#     "02 - Motion Synthesis & Animation/Data-Driven": "9IX63K42",
#     "02 - Motion Synthesis & Animation/Hybrid": "TSUETE2S",
#     "02 - Motion Synthesis & Animation/Physics-Based": "6J53XESH",
#     "03 - Biomechanics": "D9U2FKW9",
#     "03 - Biomechanics/Data-Driven": "8P2DX55B",
#     "03 - Biomechanics/Hybrid": "PZX5APZM",
#     "03 - Biomechanics/Physics-Based": "3WMN73HD",
#     "04 - Computer Vision": "XZR28X3V",
#     "04 - Computer Vision/Data-Driven": "25KQV84I",
#     "04 - Computer Vision/Hybrid": "5KTRN4AM",
#     "04 - Computer Vision/Physics-Based": "GHK8IUJV",
#     "05 - Robotics & Control": "UAP555ST",
#     "05 - Robotics & Control/Data-Driven": "7ETWRNJJ",
#     "05 - Robotics & Control/Hybrid": "NI4AGR96",
#     "05 - Robotics & Control/Physics-Based": "V2CDHMEJ",
#     "06 - Machine Learning": "M4UEQV52",
#     "06 - Machine Learning/A - Deep Learning": "ZYIRP8AX",
#     "06 - Machine Learning/A - Deep Learning/01 - DL Theory": "XBKYRUPJ",
#     "06 - Machine Learning/A - Deep Learning/02 - DL in Character Animation": "8DZ2RRGN",
#     "06 - Machine Learning/A - Deep Learning/03 - Few-Shot Learning": "GA7QLKXJ",
#     "06 - Machine Learning/A - Deep Learning/04 - Residual Networks": "XTFGVIYA",
#     "06 - Machine Learning/A - Deep Learning/05 - Permutation Invariant Architectures": "VWLJGAWW",
#     "06 - Machine Learning/A - Deep Learning/06 - Diffusion": "T6BGBVSL",
#     "06 - Machine Learning/A - Deep Learning/07 - Transformers": "69B42JZU",
#     "06 - Machine Learning/A - Deep Learning/08 - Vector Quantization": "9DPKLWE9",
#     "06 - Machine Learning/B - Reinforcement Learning": "DZXA5J2J",
#     "06 - Machine Learning/B - Reinforcement Learning/01 - RL Theory": "BJU2A5MI",
#     "06 - Machine Learning/B - Reinforcement Learning/02 - RL in Character Animation": "DC8SRPKI",
#     "06 - Machine Learning/B - Reinforcement Learning/03 - Simulation Environments": "55F3KGNR",
#     "06 - Machine Learning/B - Reinforcement Learning/04 - Policy Optimization": "825RDG7C",
#     "06 - Machine Learning/C - CNNs": "QSP3XLWZ",
#     "06 - Machine Learning/C - CNNs/01 - CNN Architectures": "8XYMF6WX",
#     "06 - Machine Learning/D - GANs": "BNF4RBUG",
#     "06 - Machine Learning/E - Adversarial Learning": "TF9DQ9NL",
#     "06 - Machine Learning/Z - Applications": "NSWXI7SN",
#     "07 - Mathematics": "Z3USHHQB",
#     "07 - Mathematics/A - Linear Algebra": "RUE27HTK",
#     "07 - Mathematics/B - ODEs": "PA5NGSFD",
#     "07 - Mathematics/C - Geometry": "QJKQW75Q",
#     "08 - Physics": "9FJ8KN8J",
#     "08 - Physics/A - Physics Simulation Basics": "UXU79JYK",
#     "08 - Physics/B - Differentiable Physics for Animation": "8SYJF58T"
# }

COLLECTION_IDS = {
    "00 - Unclassified": "2R3JBEZL",
    "01 - Digital Humans & Appearance/Data-Driven": "RDH88XA7",
    "01 - Digital Humans & Appearance/Hybrid": "GCSZPWXB",
    "01 - Digital Humans & Appearance/Physics-Based": "NWWX4PGK",
    "02 - Motion Synthesis & Animation/Data-Driven": "9IX63K42",
    "02 - Motion Synthesis & Animation/Hybrid": "TSUETE2S",
    "02 - Motion Synthesis & Animation/Physics-Based": "6J53XESH",
    "03 - Biomechanics/Data-Driven": "8P2DX55B",
    "03 - Biomechanics/Hybrid": "PZX5APZM",
    "03 - Biomechanics/Physics-Based": "3WMN73HD",
    "04 - Computer Vision/Data-Driven": "25KQV84I",
    "04 - Computer Vision/Hybrid": "5KTRN4AM",
    "04 - Computer Vision/Physics-Based": "GHK8IUJV",
    "05 - Robotics & Control/Data-Driven": "7ETWRNJJ",
    "05 - Robotics & Control/Hybrid": "NI4AGR96",
    "05 - Robotics & Control/Physics-Based": "V2CDHMEJ"
}

# 1. Get all paths except Unclassified
_all_paths = [p for p in COLLECTION_IDS.keys() if p != "00 - Unclassified"]

# 2. Filter out any path that acts as a parent to another path
VALID_FOLDERS = [
    path for path in _all_paths 
    if not any(other_path.startswith(path + "/") for other_path in _all_paths)
]