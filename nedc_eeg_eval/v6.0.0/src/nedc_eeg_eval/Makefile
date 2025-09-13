# file: $(NEDC_NFC)/util/python/nedc_eeg_eval/Makefile
#

# define source and object files
#
SRC = nedc_eeg_eval.py
EXE := $(basename $(SRC))
HLP := $(wildcard *.help)
USG := $(wildcard *.usage)
PRM = $(wildcard *.toml)

# define an installation target
#
install:
	rm -f $(NEDC_NFC)/bin/$(EXE)
	rm -f $(NEDC_NFC)/docs/help/$(HLP)
	rm -f $(NEDC_NFC)/docs/usage/$(USG)
	rm -f $(NEDC_NFC)/docs/params/$(PRM)

	cp -f $(SRC) $(NEDC_NFC)/bin/$(EXE)
	chmod u+rwx,g+rwx,o+rx $(NEDC_NFC)/bin/$(EXE)

	cp -f $(HLP) $(NEDC_NFC)/docs/help/$(HLP)
	chmod u+rw,g+rw,o+r $(NEDC_NFC)/docs/help/$(HLP)

	cp -f $(USG) $(NEDC_NFC)/docs/usage/$(USG)
	chmod u+rw,g+rw,o+r $(NEDC_NFC)/docs/usage/$(USG)

	cp -f $(PRM) $(NEDC_NFC)/docs/params/$(PRM)
	chmod u+rw,g+rw,o+r $(NEDC_NFC)/docs/params/$(PRM)

#
# end of file
