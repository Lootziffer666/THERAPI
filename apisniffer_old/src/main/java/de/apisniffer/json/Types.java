package de.apisniffer.json;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.lang.reflect.Field;
import java.lang.reflect.ParameterizedType;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * Enum of all supported target-field types.
 *
 * Each constant implements {@link #setValue} to extract a value from the JSON
 * object graph and assign it to the field in a type-specific way.
 *
 * Two boolean flags govern the behaviour:
 * <ul>
 *   <li><b>override</b> – if {@code true}, an already-populated field is
 *       overwritten; if {@code false}, the field is only written when it is
 *       still {@code null} (or, for primitives, at its default value).</li>
 *   <li><b>lenient</b> – if {@code true}, a type mismatch between the JSON
 *       value and the target field triggers a conversion attempt instead of
 *       silently skipping the field.</li>
 * </ul>
 *
 * The recursive depth-first search through the JSON object graph is performed
 * by Jackson's own {@link ObjectNode#findValue(String)}, which visits every
 * node in the tree until the first match on the field name is found.
 */
public enum Types {

    // -----------------------------------------------------------------------
    // Primitive / wrapper types
    // -----------------------------------------------------------------------

    STRING {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && value.isTextual())) {
                if (override || field.get(object) == null) {
                    field.set(object, value != null ? value.asText() : null);
                }
            }
        }
    },

    BOOLEAN {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && value.isBoolean())) {
                if (override || isUnset(object, field)) {
                    if (value != null) {
                        field.set(object, value.asBoolean());
                    }
                }
            }
        }
    },

    INTEGER {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && (value.isInt() || value.isShort()))) {
                if (override || isUnset(object, field)) {
                    if (value != null) {
                        field.set(object, value.asInt());
                    }
                }
            }
        }
    },

    LONG {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && (value.isLong() || value.isInt()))) {
                if (override || isUnset(object, field)) {
                    if (value != null) {
                        field.set(object, value.asLong());
                    }
                }
            }
        }
    },

    DOUBLE {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && value.isDouble())) {
                if (override || isUnset(object, field)) {
                    if (value != null) {
                        field.set(object, value.asDouble());
                    }
                }
            }
        }
    },

    FLOAT {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && value.isFloat())) {
                if (override || isUnset(object, field)) {
                    if (value != null) {
                        field.set(object, (float) value.asDouble());
                    }
                }
            }
        }
    },

    // -----------------------------------------------------------------------
    // Nested object: recurse into the FULL JSON tree so that DFS can still
    // locate any field anywhere in the graph, regardless of nesting level.
    // -----------------------------------------------------------------------

    OBJECT {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (lenient || (value != null && value.isObject())) {
                if (override || field.get(object) == null) {
                    Object nested = field.getType().getDeclaredConstructor().newInstance();
                    // Pass the FULL node so DFS continues across the whole tree.
                    JsonMapper.fillObject(nested, node, override, lenient);
                    field.set(object, nested);
                }
            }
        }
    },

    // -----------------------------------------------------------------------
    // Collections (List, Set, …): element type resolved via generics.
    // -----------------------------------------------------------------------

    COLLECTION {
        @Override
        public void setValue(Object object, Field field, ObjectNode node,
                             boolean override, boolean lenient) throws Exception {
            JsonNode value = node.findValue(field.getName());
            if (value == null || !value.isArray()) {
                return;
            }
            if (override || field.get(object) == null) {
                Class<?> elementType = resolveElementType(field);
                List<Object> list = new ArrayList<>();
                for (JsonNode element : value) {
                    Object converted = convertElement(element, elementType, lenient);
                    if (converted != null) {
                        list.add(converted);
                    }
                }
                field.set(object, list);
            }
        }

        private Class<?> resolveElementType(Field field) {
            if (field.getGenericType() instanceof ParameterizedType) {
                ParameterizedType pt = (ParameterizedType) field.getGenericType();
                return (Class<?>) pt.getActualTypeArguments()[0];
            }
            return Object.class;
        }

        private Object convertElement(JsonNode element, Class<?> target, boolean lenient) {
            if (target == String.class)                        return element.asText();
            if (target == Boolean.class || target == boolean.class) return element.asBoolean();
            if (target == Integer.class || target == int.class)     return element.asInt();
            if (target == Long.class    || target == long.class)    return element.asLong();
            if (target == Double.class  || target == double.class)  return element.asDouble();
            if (target == Float.class   || target == float.class)   return (float) element.asDouble();
            if (lenient)                                             return element.asText();
            return null;
        }
    };

    // -----------------------------------------------------------------------
    // Shared helper
    // -----------------------------------------------------------------------

    /**
     * Returns {@code true} when the field should be written in non-override
     * mode: always for primitives (no meaningful "already set" state), and
     * when the field reference is {@code null} for object types.
     */
    protected boolean isUnset(Object object, Field field) throws IllegalAccessException {
        if (field.getType().isPrimitive()) {
            return true; // primitives have no null; treat as always writable
        }
        return field.get(object) == null;
    }

    // -----------------------------------------------------------------------
    // Factory
    // -----------------------------------------------------------------------

    /**
     * Resolves the {@code Types} constant for the given field class.
     *
     * <ol>
     *   <li>Collection subtypes → {@link #COLLECTION}</li>
     *   <li>Primitives and {@code java.*} types → enum constant by simple name
     *       ({@code int} → {@code INTEGER}); unknown java types fall back to
     *       {@link #STRING}.</li>
     *   <li>Everything else → {@link #OBJECT}</li>
     * </ol>
     */
    public static Types getType(Class<?> clazz) {
        if (Collection.class.isAssignableFrom(clazz)) {
            return COLLECTION;
        }
        if (clazz.isPrimitive()
                || (clazz.getPackage() != null
                    && clazz.getPackage().getName().startsWith("java."))) {
            String name = clazz.getSimpleName().toUpperCase();
            if ("INT".equals(name)) {
                name = "INTEGER";
            }
            try {
                return Types.valueOf(name);
            } catch (IllegalArgumentException e) {
                return STRING; // e.g. Date, LocalDate – best-effort text conversion
            }
        }
        return OBJECT;
    }

    /** Type-specific field assignment. */
    public abstract void setValue(Object object, Field field, ObjectNode node,
                                  boolean override, boolean lenient) throws Exception;
}
