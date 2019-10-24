default:
	make -j8 test

# rpi3
rpi3_0:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_0.log

rpi3_1:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_1.log

rpi3_2:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_2.log

rpi3_3:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_3.log


# rpi2
rpi2_0:
	./tests/test_rpi.py rpi2 -v > logs/test_rpi2_0.log

rpi2_1:
	./tests/test_rpi.py rpi2 -v > logs/test_rpi2_1.log

test: rpi3_0 rpi3_1 rpi3_2 rpi3_3 rpi2_0 rpi2_1


.PHONY: default test rpi3_0 rpi3_1 rpi3_2 rpi3_3 rpi2_0 rpi2_1

