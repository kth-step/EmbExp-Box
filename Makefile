default:
	make -j16 test

# rpi4
test_rpi4_0:
	./tests/test_rpi.py rpi4 -v > logs/test_rpi4_0.log

test_rpi4_1:
	./tests/test_rpi.py rpi4 -v > logs/test_rpi4_1.log

# rpi3
test_rpi3_0:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_0.log

test_rpi3_1:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_1.log

test_rpi3_2:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_2.log

test_rpi3_3:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_3.log

test_rpi3_4:
	./tests/test_rpi.py rpi3 -v > logs/test_rpi3_4.log


# rpi2
test_rpi2_0:
	./tests/test_rpi.py rpi2 -v > logs/test_rpi2_0.log

test_rpi2_1:
	./tests/test_rpi.py rpi2 -v > logs/test_rpi2_1.log


test: test_rpi4_0 test_rpi4_1 test_rpi3_0 test_rpi3_1 test_rpi3_2 test_rpi3_3 test_rpi3_4 test_rpi2_0 test_rpi2_1


.PHONY: default test
.PHONY: test_rpi4_0 test_rpi4_1
.PHONY: test_rpi3_0 test_rpi3_1 test_rpi3_2 test_rpi3_3 test_rpi3_4
.PHONY: test_rpi2_0 test_rpi2_1

