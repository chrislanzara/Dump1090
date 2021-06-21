/**\file    sdrplay.h
 * \ingroup Main
 */
#ifndef SDRPLAY_LOADER_H
#define SDRPLAY_LOADER_H

#include <stdint.h>

typedef struct SDRplay_info sdrplay_dev;

typedef void (*sdrplay_cb) (uint8_t *buf, uint32_t len, void *ctx);

extern int sdrplay_init (const char *name, sdrplay_dev **device);
extern int sdrplay_exit (sdrplay_dev *device);

extern const char *sdrplay_strerror (int rc);

extern int sdrplay_cancel_async (sdrplay_dev *device);

extern int sdrplay_read_async (sdrplay_dev *device,
                               sdrplay_cb   cb,
                               void        *ctx,
                               uint32_t     buf_num,
                               uint32_t     buf_len);

#endif /* SDRPLAY_LOADER_H */