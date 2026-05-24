#define _GNU_SOURCE

#include <dlfcn.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static void *(*real_malloc)(size_t);
static void *(*real_calloc)(size_t, size_t);
static void (*real_free)(void *);
static __thread int in_hook;

static void init_hooks(void) {
    if (real_malloc) {
        return;
    }

    real_malloc = dlsym(RTLD_NEXT, "malloc");
    real_calloc = dlsym(RTLD_NEXT, "calloc");
    real_free = dlsym(RTLD_NEXT, "free");
}

void *malloc(size_t size) {
    init_hooks();
    void *ptr = real_malloc(size);
    if (!in_hook) {
        in_hook = 1;
        fprintf(stderr, "[mtrace] malloc(%#zx) = %p\n", size, ptr);
        in_hook = 0;
    }
    return ptr;
}

void *calloc(size_t nmemb, size_t size) {
    init_hooks();
    void *ptr = real_calloc(nmemb, size);
    if (!in_hook) {
        in_hook = 1;
        fprintf(stderr, "[mtrace] calloc(%#zx, %#zx) = %p\n", nmemb, size, ptr);
        in_hook = 0;
    }
    return ptr;
}

void free(void *ptr) {
    init_hooks();
    if (!in_hook) {
        in_hook = 1;
        fprintf(stderr, "[mtrace] free(%p)\n", ptr);
        in_hook = 0;
    }
    real_free(ptr);
}
