from dogpile.cache import make_region

from . import env


if env.name == 'dev':
    region = make_region().configure(
        'dogpile.cache.memory',
        expiration_time=300
    )

else:
    region = make_region().configure(
        'dogpile.cache.redis',
        arguments = {
            'host': '127.0.0.1',
            'port': 6379,
            'db': 0,
            'redis_expiration_time': 1800, # 30 min
            'distributed_lock': True
        }
    )
