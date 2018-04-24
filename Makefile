# based on https://github.com/KDahlgren/pyLDFI/blob/master/Makefile

all: deps

deps: get-submodules c4 molly

clean:
	rm -rf lib/c4/build
	rm -rf lib/molly

cleanc4:
	rm -rf lib/c4/build

cleanmolly:
	rm -rf lib/molly

c4: lib/c4/build/src/libc4/libc4.dylib

lib/c4/build/src/libc4/libc4.dylib:
	@which cmake > /dev/null
	cd lib/c4 && mkdir -p build
	cd lib/c4/build && cmake ..
	( cd lib/c4/build && make ) 2>&1 | tee c4_out.txt;
	rm c4_out.txt

molly:
	cd lib/molly/ ; make ; cp lib/c4/build/src/libc4/libc4.dylib . ;

get-submodules:
	git submodule init
	git submodule update

