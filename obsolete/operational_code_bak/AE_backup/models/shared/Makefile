include ../Makefile.common

INCLUDE_FILES=dataset_3.h shared_argument.h shared_list.h shared_types.h \
	shared_interpolate.h shared_tree.h shared_vector.h sunang.h \
	Achl.hh Alpha.hh Aph.hh Aw.hh Bw.hh Beta.hh Chl.hh Ed.hh \
	Environment.hh K.hh Ab.hh Kc.hh Kw.hh Observer.hh Pbm.hh PhiMax.hh Raster.hh \
	St.hh
DLIBRARIES_LIST=libproof_shared.so libproof_shared++.so
DLIBRARIES=$(DLIBRARIES_LIST:%=$(BUILD_DIR)/%)
SLIBRARIES_LIST=libproof_shared.a libproof_shared++.a
SLIBRARIES=$(SLIBRARIES_LIST:%=$(BUILD_DIR)/%)
LIBRARIES=$(DLIBRARIES) $(SLIBRARIES)
PROOF_SHARED_OBJ_LIST=dataset_3.o shared_argument.o shared_list.o \
	shared_vector.o shared_interpolate.o shared_tree.o sunang.o
PROOF_SHARED_OBJ=$(PROOF_SHARED_OBJ_LIST:%=$(BUILD_DIR)/%)
PROOF_SHAREDXX_OBJ_LIST=Achl.o Alpha.o Aph.o Aw.o Bw.o Beta.o Chl.o Ed.o \
	Environment.o K.o Ab.o Kc.o Kw.o Observer.o Pbm.o PhiMax.o Raster.o St.o
PROOF_SHAREDXX_OBJ=$(PROOF_SHAREDXX_OBJ_LIST:%=$(BUILD_DIR)/%)

all: $(LIBRARIES)

clean:
	-@rm -f $(PROOF_SHARED_OBJ)
	-@rm -f $(PROOF_SHAREDXX_OBJ)
	-@rm -f $(LIBRARIES)

rebuild: clean all

install: all
	@mkdir -p $(LIB_DIR)
	-@echo Installing $(LIBRARIES) into $(LIB_DIR)
	\cp -f $(LIBRARIES) $(LIB_DIR)
	-@echo Installing $(INCLUDE_FILES) into $(INC_DIR)
	\cp -f $(INCLUDE_FILES) $(INC_DIR)

# proof_shared ---------------------------------------------
$(BUILD_DIR)/libproof_shared.so: $(PROOF_SHARED_OBJ)
	-@echo Building $(@F)
	$(LINK_DLIB) $@ $(PROOF_SHARED_OBJ) -lm

$(BUILD_DIR)/libproof_shared.a: $(PROOF_SHARED_OBJ)
	-@echo Building $(@F)
	$(LINK_SLIB) $@ $(PROOF_SHARED_OBJ)

# proof_shared++ ---------------------------------------------
$(BUILD_DIR)/libproof_shared++.so: $(PROOF_SHAREDXX_OBJ)
	-@echo Building $(@F)
	$(LINK_DLIBXX) $@ $(PROOF_SHAREDXX_OBJ) -lm

$(BUILD_DIR)/libproof_shared++.a: $(PROOF_SHAREDXX_OBJ)
	-@echo Building $(@F)
	$(LINK_SLIB) $@ $(PROOF_SHAREDXX_OBJ)
