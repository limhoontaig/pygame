MAJOR = 0
MINOR = 0
REVISION = 1

def gen_class():
    MAJOR = 0
    MINOR = 4
    REVISION = 2

    class Language:
        MAJOR = 3
        MINOR = 7
        REVISION = 4

        def version(self):
            MAJOR = 3
            MINOR = 7
            REVISION = 4
            return '{}.{}.{}'.format(MAJOR, MINOR, REVISION)
    
    return Language()

lang = gen_class()
language = lang.version()

print(language)