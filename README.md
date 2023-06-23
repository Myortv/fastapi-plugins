# fastapi-plugins
Simplified version of plugins from Rolefr for fastapi. Contains plugins for asyncpg, pyignite and other.

# Api Reference
Check examples dir, to see minimal running examples.

## Caching
### plugins.cache.base.CacheManagerBase (AbstractPlugin)
> **CacheManagerBase** is parent for all plugins cache managers. You only need to start **CacheManagerBase** and all child managers will work too (they use **CacheManagerBase** **Config** and behavior)

#### \_\_init__(self, default_binder: ConfigMaker, list_binders: List[ConfigMaker] | None = None, single_binders: List[ConfigMaker] | None = None )
Creates minimal instance of cache manager. It needs to run **connect_manager** before work start.

#### *asynс* start(self)
Starts caching plugin. Creates connections client, with **Configs.NODES** and save client to **Configs.IGNITE_CLIENT**

#### *async* stop(self)
Stops caching plugin. Close Ignite connection.

#### *async* connect_manager(self)
Creates cache connections for all manager's **binders**.
#### *async* get(binder: Binder | PageBinder, key_value: str | int)
Static method provides minimal get behavior. Return parsed with **Binder.object.model** data from cache.
#### *async* set(binder: Binder | PageBinder, data: 'Pydantic Model', key_value: str | int | None = None)
**key_value** - ignite cache key, data stored with thise value.
Static method provides minimal set behavior. If **key_value** not setted trying to get value with **Binder.object.key_field**. **Page** or **ListBinders** can be used only with setted **key_value**.
#### *async* delete(binder: Binder | PageBinder, data: 'Pydantic Model', key_value: str | int | None = None)
Static method provides minimal deletion behavior. Calculates **key_value** as **set** does.

#### *class* Config
> **Config** is one for all cache managers. Changes in *Config* affects on whole plugin.

`CahceMnagerBase.Config.IGNITE_CLIENT (AioClient|None=None)` 
Client for all plugins connections. Can be setted by hands instead using **CacheManagerBase.start**

`CacheManagerBase.Config.NODES (List)`
List of default ignite nodes needed for connections.

### plugins.cache.generic.GenericBase(CacheManagerBase)
> **GenericBase** implements loops and calls, that designed to be easly overridden with **mixins**, to get flexibility in cache_manager behavior.

#### *async* replace(self, binder: Binder, data: Pydantic Model)
Just an alias for **self.set** (probably **CacheManager Base.set**) and needed for easy overriding.

#### *async* save_proc(self, data: 'Pydantic Model') -> None
Process of saving data to cache.
Consists of two key functions: **set** and **set_list**, that applied to single and list caches.
Thise key functions can be overridden with mixins.

#### *async* update_proc(self, data: 'Pydantic Model') -> None
Process of updating data in cache.
Consists of two key functions: **replace** and **replace_list**, that applied to single and list caches.
Thise key functions can be overridden with mixins.

#### *async* delete_proc(self, data: 'Pydantic Model') -> None
Proccess of deleting data from cache.
Consists of two key functions: **delete** and **delete_list**, that applied to single and list caches.
Thise key functions can be overridden with mixins.

### plugins.cache.generic.GenericDecorator

#### *decorator* get_dec(self, cache_name: str | None = None)
**cache_name** - name of cache (like 'projects') needed in operation. If **cache_name** is empty, uses **CacheManger.default_binder**.
**get_dec** not only gets data from cache, it contains all logic needed (trying to get cached data, and if it's not exists, saving data to cache after controller call).

#### *decorator* post_dec(self)
Decorator that saves data from controller to cache. Just calls **self.save_proc** (probably **GenericBase.save_proc**).

#### *decorator* put_dec(self)
Decorator that updates data in cache. Just calls **self.update_proc** (probably **GenericBase.update_proc**).

#### *decorator* put_dec(self)
Decorator that updates data in cache. Just calls **self.update_proc** (probably **GenericBase.update_proc**).

### plugins.cache.mixins.WipingPageMixin(BaseMixin)
> **Mixin** overrides **set_list**, **replace_list** and **delete_list** to add wiping behavior. When any data is created, deleted or needs update, **WipingPageMixin** will delete all corresponding listed(paged) data.

|  function | is overriden  |
| ------------ | ------------ |
|  set  |  ❌ |
|  set_list |  ✅ |
|  replace |  ❌ |
|  replace list |  ✅ |
|  delete |  ❌ |
|  delete_list |  ✅ |

### plugins.cache.datatypes.ConfigMaker
> Datatype needed to easly create, store and manage cache_managers **binders** config properties. Mostly used by clients (in microservice code)

| field  | field description  |
| ------------ | ------------ |
| **cache_name**  | name of cache, 'projects' or 'cases-storyline' for example.|
| **key_field**  | if stored object is not **page**, **key_field** should be equal to name of field containts **key_value** for storing in cache ('id' or 'name'). If stored object is **page**, so **key_field** should be name of field stores nested items ('items'). |
| **model**  | stores pydantic model of stored data (page if stored data is page). |
| **item_key_field**  |  *optional*. If stored data is **page**, this field may contain nested items **key_value** that used for storing in cache ('id' or 'name')|
|  **item_model** |  *optional*. If stored data is **page**, **item_key_field** may contain pydantic model of nested object|

**For Pages:**
`ConfigMaker('page_cache', 'items', PageModel, 'id', 'SomeModel')`
**For other objects:**
`ConfigMaker('cache_name', 'id', SomeModel)`

So you can see, that ConfigMaker has 2 parts, as stored in cache object can contain 2 parts.
```
key: {'id': 1, 'name': 'Lain'}
key: {
	'items':[
		{'id': 1, 'name': 'Lain'},
		{'id': 2, 'name': 'Ichise'}
	], '
	total'
}
```
And first part (**cache_name, key_field, model**) needed to describe stored in cache object, and second part (item_key_field, item_model) needed to describe optional nested object.

### How use plugin

Firstly you need start **CacheManagerBase**.
Probably you also need to connect your manager in controllers code, so save app to your Config class.
if you will start contollers cache_manager in controoler code, make sure, CacheManagerBase.start() called before routers import.
```python
# main.py 
from plugins import CacheManagerBase

@app.on_event('startup')
async def start_plugin():
	CacheManagerBase.start()

Config.APP = app

# (probably routs import and other staff here)

@app.on_event('shutdown')
async def stop_plugin():
	CacheManagerBase.start()
```
Then, we can go to the controller. We'll setup cache_manager as decorator.
```python
# controller.py
from plugins import (
    GenericDecorator,
    WipingPageMixin,
    CacheConfigMaker as CM,
)

from app.models import SomeModel, PageModel
from utils import Config


class CacheManager(GenericDecorator, WipingPageMixin):
    pass

cache_manager = CacheManager(
	default_binder=CM('cache_name', 'id', SomeModel),
	list_binders=[
		CM('other_cache_name', 'pages field with items', PageModel, 'value', SomeModel)
	]
)

@Configs.APP.on_event('startup')
async def connect_cache_manager():
	global cache_manager
	await cache_manager.connect_manager()


@cache_manager.get_dec()
async def some_controller(id):
	pass
```

### Log
**WIP**
### Requests
**WIP**
### Dep module
**WIP**

# Install package
You need setuptools installed.

```
pip install setuptools
```

If setuptools already installed, ust run command below in root dir, to install rolefr-plugins.

```
pip install .
```

To upgrade pakage, run:

```
pip install --upgrade .
```

To delete pakage simply run:

```
pip uninstall rolefr-plugins
```

---

Installation process uses legacy way to build pakage, so it needs to be updated.

Links
---
[little tutorial i used to build pakage](https://betterscientificsoftware.github.io/python-for-hpc/tutorials/python-pypi-packaging/)

[setuptools official docs](https://setuptools.pypa.io/en/latest/index.html)
>>>>>>> dcb5022 (init commit)
