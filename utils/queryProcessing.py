def queryPreprocessing(query: str):
    query = query.lower().strip()
    # query = correctSpelling(query)
    query = removeAbbreviations(query)
    query = fixContractions(query)
    query = fixSlangs(query)
    return query


# from spellchecker import SpellChecker

# spell = SpellChecker()


# def correctSpelling(query: str):
#     words = query.split()
#     modified = [
#         spell.correct(word) if word in spell.unknown(words) else word for word in words
#     ]
#     return modified


import spacy
from scispacy.abbreviation import AbbreviationDetector

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Add abbreviation detector by factory string (SpaCy creates instance internally)
if "abbreviation_detector" not in nlp.pipe_names:
    nlp.add_pipe("abbreviation_detector")  # no need to create instance yourself


# Function to expand abbreviations
def removeAbbreviations(query: str):
    doc = nlp(query)
    altered_tok = [tok.text for tok in doc]

    for abrv in doc._.abbreviations:
        if abrv._.long_form is not None:
            start, end = abrv.start, abrv.end
            long_form_tokens = str(abrv._.long_form).split()
            altered_tok[start:end] = long_form_tokens

    return " ".join(altered_tok)


import contractions


def fixContractions(query: str):
    modified =  contractions.fix(query)
    if type(modified) == str:
        return modified
    elif type(modified) == tuple:
        return " ".join(modified)


from utils.slangDictionary import abbreviations

def fixSlangs(query: str):
    words = query.split()
    modified = [
        abbreviations[word] if word in abbreviations.keys() else word for word in words
    ]
    return " ".join(modified)



import emoji


def handleEmoji(query: str):
    modified = [
        emoji.demojize(word) if emoji.is_emoji(word) else word for word in query.split()
    ]
    return " ".join(modified)

