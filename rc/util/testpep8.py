# import subprocess


# def test_pep8():  # no-coverage
#    """
#    Make sure pep-8 passes
#    """
#    pep8 = subprocess.Popen(["pep8",
#                             "--exclude=./rc/tdu/,"
#                             "./docs/conf.py",
#                             "-r", "."],
#                            stdout=subprocess.PIPE).communicate()[0]
#    if pep8:
#        print pep8
#        raise Exception("PEP-8 error found")
