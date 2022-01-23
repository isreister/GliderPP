include ../Makefile.common

BINARIES_LIST=par
BINARIES=$(BINARIES_LIST:%=$(BUILD_DIR)/%)
PAR_OBJ_LIST=par.o par_argument.o \
	par_calculate.o par_model.o \
	par_readmodel.o
PAR_OBJ=$(PAR_OBJ_LIST:%=$(BUILD_DIR)/%)

all: $(BINARIES)

clean:
	-@rm $(BINARIES)
	-@rm $(PAR_OBJ)

rebuild: clean all

install: all
	@mkdir -p $(EXEC_DIR)
	-@echo Installing $(BINARIES) into $(EXEC_DIR)
	\cp -f $(BINARIES) $(EXEC_DIR)

# gplatt92 ---------------------------------------------
$(BUILD_DIR)/par: $(PAR_OBJ)
	-@echo Building $(@F)
	$(LINK_EXEC) $@ $(PAR_OBJ) -lproof_shared -lm
