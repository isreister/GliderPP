include ../Makefile.common

BINARIES_LIST=morel91
BINARIES=$(BINARIES_LIST:%=$(BUILD_DIR)/%)
MOREL91_OBJ_LIST=morel91.o morel91_argument.o \
	morel91_calculate.o morel91_model.o
MOREL91_OBJ=$(MOREL91_OBJ_LIST:%=$(BUILD_DIR)/%)

all: $(BINARIES)

clean:
	-@rm $(BINARIES)
	-@rm $(MOREL91_OBJ)

rebuild: clean all

install: all
	@mkdir -p $(EXEC_DIR)
	-@echo Installing $(BINARIES) into $(EXEC_DIR)
	\cp -f $(BINARIES) $(EXEC_DIR)

# morel91 ---------------------------------------------
$(BUILD_DIR)/morel91: $(MOREL91_OBJ)
	-@echo Building $(@F)
	$(LINK_EXECXX) $@ $(MOREL91_OBJ) -lproof_shared -lproof_shared++ -lz -lm
