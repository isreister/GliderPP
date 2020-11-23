/* shared_types.h
 * 
 * Shared type definitions used in shared code.
 * 
 * Latest modification: 00/10/26
 */

#ifndef _SHARED_TYPES
#define _SHARED_TYPES

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * A type that must be able to store values for either wavelength or time.
 */
typedef float PositionType;

/**
 * A type that must be able to store values for either irradiance, chlorophyll,
 *  pbm, alpha, beta, k or prime production.
 */
typedef float ValueType;

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif
