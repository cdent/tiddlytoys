
PLUGINS = sqlstore/sql.py twstatic/static.py formreader/formreader.py whoosh/whoosher.py

all:
	@echo "I dont know what to do"

clean:
	rm -f store.db
	find . -type l -exec rm {} \;
	rm -rf dist build jack.egg-info

getplugins:
	for i in $(PLUGINS); do \
	    ln -s ../../tiddlyweb-plugins/$$i; \
	done
	mkdir static

bags:
	twanager bag bag0 </dev/null
	twanager bag bag1 </dev/null

recipes:
	twanager recipe recipe1 < recipe1

sample:
	twanager tiddler bag0 house1 < house1
	twanager tiddler bag0 house2 < house2

resetup: clean getplugins bags recipes

sdist: clean getplugins
	python setup.py sdist
