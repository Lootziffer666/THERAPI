package de.apisniffer.json;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

/**
 * Generic JSON-to-object mapper that locates field values anywhere in the JSON
 * object graph via recursive depth-first search.
 *
 * <p>The DFS is delegated to Jackson's {@link com.fasterxml.jackson.databind.JsonNode#findValue(String)},
 * which searches the entire sub-tree for the first node whose key matches the
 * target field name. This means source and target classes need not share the
 * same structure: only the <em>names</em> (and, in strict mode, the <em>types</em>)
 * of the fields must agree.</p>
 *
 * <h3>Example – flattening a nested structure</h3>
 * <pre>
 * // JSON from Mitarbeiter-Service (nested)
 * {
 *   "personalnummer": 42,
 *   "vorname": "Anna",
 *   "betriebsstelle": { "betriebsstellenname": "Hamburg" },
 *   "anmeldung":      { "standarddrucker": "HP-1234" }
 * }
 *
 * // Target POJO in Druck-Service (flat)
 * Auftraggeber auftraggeber =
 *     JsonMapper.getAvailableFromJson(json, Auftraggeber.class, false, false);
 * // auftraggeber.betriebsstellenname == "Hamburg"  ← found 2 levels deep
 * // auftraggeber.standarddrucker     == "HP-1234"  ← found 2 levels deep
 * </pre>
 *
 * <h3>Flags</h3>
 * <ul>
 *   <li><b>override</b> – overwrite non-null fields that are already populated.</li>
 *   <li><b>lenient</b> – attempt type conversion when source and target types
 *       differ (e.g. {@code boolean → String}, {@code Long → Integer}).</li>
 * </ul>
 */
public final class JsonMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private JsonMapper() {
    }

    /** Exposes the shared ObjectMapper for serialization (e.g. in tests). */
    public static ObjectMapper getObjectMapper() {
        return OBJECT_MAPPER;
    }

    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------

    /**
     * Maps fields from {@code json} to {@code object} in-place and returns it.
     *
     * @param json     JSON source string
     * @param object   pre-existing target object
     * @param override overwrite already-populated fields
     * @param lenient  attempt type conversion on mismatch
     */
    public static <E> E getAvailableFromJson(String json, E object,
                                             boolean override, boolean lenient) {
        try {
            ObjectNode objectNode = OBJECT_MAPPER.readValue(json, ObjectNode.class);
            fillObject(object, objectNode, override, lenient);
            return object;
        } catch (JsonMappingException e) {
            throw e;
        } catch (Exception e) {
            throw new JsonMappingException(
                    "Failed to map JSON to " + object.getClass().getSimpleName(), e);
        }
    }

    /**
     * Instantiates {@code clazz} via its no-arg constructor, then delegates to
     * {@link #getAvailableFromJson(String, Object, boolean, boolean)}.
     */
    public static <E> E getAvailableFromJson(String json, Class<E> clazz,
                                             boolean override, boolean lenient) {
        try {
            return getAvailableFromJson(json, clazz.getDeclaredConstructor().newInstance(),
                                        override, lenient);
        } catch (JsonMappingException e) {
            throw e;
        } catch (Exception e) {
            throw new JsonMappingException(
                    "Could not instantiate " + clazz.getSimpleName(), e);
        }
    }

    // -----------------------------------------------------------------------
    // Package-private: called recursively by Types.OBJECT
    // -----------------------------------------------------------------------

    /**
     * Iterates over all declared fields of {@code object} (including inherited
     * ones) and delegates to the matching {@link Types} constant.
     *
     * <p>Passing the <em>full</em> {@code objectNode} – rather than a sub-node –
     * is what enables the depth-first search: each nested object receives the
     * entire JSON tree, so {@code findValue} can still reach any field at any
     * depth.</p>
     */
    static void fillObject(Object object, ObjectNode objectNode,
                           boolean override, boolean lenient) {
        for (Field field : allFields(object.getClass())) {
            field.setAccessible(true);
            try {
                Types.getType(field.getType())
                     .setValue(object, field, objectNode, override, lenient);
            } catch (Exception e) {
                throw new JsonMappingException(
                        "Error mapping field '" + field.getName()
                        + "' in " + object.getClass().getSimpleName(), e);
            }
        }
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    /** Collects declared fields from the class hierarchy (excluding Object). */
    private static List<Field> allFields(Class<?> clazz) {
        List<Field> fields = new ArrayList<>();
        for (Class<?> c = clazz; c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field f : c.getDeclaredFields()) {
                fields.add(f);
            }
        }
        return fields;
    }
}
