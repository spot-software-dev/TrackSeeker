import requests


def recognize(user_music, compared_music):
    raise NotImplementedError


#   TODO: Catch Errors
#    Calls to the library can raise AcoustidError exceptions of two subtypes:
#      FingerprintGenerationError and WebServiceError.
#    Catch these exceptions if you want to proceed when audio can't be decoded or no match is found on the server.
#    NoBackendError, a subclass of FingerprintGenerationError,
#    is used when the Chromaprint library or fpcalc command-line tool cannot be found)
