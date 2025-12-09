To convert a JSON array into a string representation of the elements in the specified format, we can create a function that processes each object in the array and returns a comma-separated list of the objects' values.

Here's an implementation of such a function:

```javascript
function jsonToArray(elements) {
  return elements.map(obj => 
    obj.map((key, value) => `${value}, ${key}: ${value}`).join(', ') 
  );
}
```

This function will take an array of objects and convert them into a string where each object is listed with its key-value pairs separated by commas. For example:

```json
[
  { "name": "A task...23", "start_time": ... },
  // ...
]
```

would be converted to

`[object1, object2, ..., objectN]`.

The function works as follows:
1. It maps over each object in the input array.
2. For each object, it maps over its properties.
3. Each property-value pair is joined with ", " and wrapped in ${value}, ${key}: ${value}.
4. The resulting string is joined with ', ' to create a comma-separated list.

This implementation ensures that all objects are processed and their values converted into the desired format.