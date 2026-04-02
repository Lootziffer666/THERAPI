package de.apisniffer.json;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for {@link JsonMapper}.
 *
 * The domain model mirrors the article's example:
 *   Mitarbeiter-Service  →  Druck-Service
 *   Mitarbeiter (nested) →  Auftraggeber (flat)
 */
class JsonMapperTest {

    // -----------------------------------------------------------------------
    // Domain model – Mitarbeiter-Service side
    // -----------------------------------------------------------------------

    static class Mitarbeiter {
        public Long          personalnummer;
        public String        vorname;
        public String        nachname;
        public Betriebsstelle betriebsstelle;
        public Anmeldung     anmeldung;
    }

    static class Betriebsstelle {
        public String  betriebsstellenname;
        public String  standort;
        public Integer betriebsstellenId;
    }

    static class Anmeldung {
        public String drucker;
        public String standarddrucker;
    }

    // -----------------------------------------------------------------------
    // Domain model – Druck-Service side (flat)
    // -----------------------------------------------------------------------

    static class Auftraggeber {
        public Long   personalnummer;
        public String vorname;
        public String nachname;
        public String betriebsstellenname; // lives in Betriebsstelle in Mitarbeiter JSON
        public String standarddrucker;     // lives in Anmeldung in Mitarbeiter JSON
    }

    // -----------------------------------------------------------------------
    // Type-conversion test classes (article diagram 3)
    // -----------------------------------------------------------------------

    static class A {
        public boolean        a;
        public Boolean        b;
        public int            c;
        public long           d;
        public List<Boolean>  e;
    }

    static class B {
        public String        a;
        public int           b;
        public Long          c;
        public int           d;
        public List<String>  e;
    }

    // -----------------------------------------------------------------------
    // Tests
    // -----------------------------------------------------------------------

    @Test
    void simpleFieldMapping() {
        String json = "{\"vorname\":\"Max\",\"nachname\":\"Mustermann\","
                    + "\"personalnummer\":12345}";

        Mitarbeiter m = JsonMapper.getAvailableFromJson(json, Mitarbeiter.class, false, false);

        assertEquals("Max",        m.vorname);
        assertEquals("Mustermann", m.nachname);
        assertEquals(12345L,       m.personalnummer);
    }

    /**
     * Core feature: the DFS (via Jackson's findValue) locates
     * {@code betriebsstellenname} and {@code standarddrucker} that are nested
     * two levels deep in the Mitarbeiter JSON and maps them into the flat
     * Auftraggeber POJO.
     */
    @Test
    void deepFieldMappingViaDFS() {
        String json = "{"
                + "\"personalnummer\":42,"
                + "\"vorname\":\"Anna\","
                + "\"nachname\":\"Schmidt\","
                + "\"betriebsstelle\":{"
                +   "\"betriebsstellenname\":\"Hamburg\","
                +   "\"standort\":\"HH-City\","
                +   "\"betriebsstellenId\":7"
                + "},"
                + "\"anmeldung\":{"
                +   "\"drucker\":\"HP-1234\","
                +   "\"standarddrucker\":\"HP-1234\""
                + "}"
                + "}";

        Auftraggeber a = JsonMapper.getAvailableFromJson(json, Auftraggeber.class, false, false);

        assertEquals(42L,       a.personalnummer);
        assertEquals("Anna",    a.vorname);
        assertEquals("Schmidt", a.nachname);
        assertEquals("Hamburg", a.betriebsstellenname); // ← from nested betriebsstelle
        assertEquals("HP-1234", a.standarddrucker);     // ← from nested anmeldung
    }

    /**
     * Verifies the bidirectional type transformation shown in article figure 3:
     * A → JSON → B → JSON → A, with lenient conversion.
     */
    @Test
    void bidirectionalTypeTransformationLenient() throws Exception {
        ObjectMapper om = JsonMapper.getObjectMapper();

        A a1 = new A();
        a1.a = false;
        a1.b = Boolean.TRUE;
        a1.c = 9824598;
        a1.d = 984L;
        a1.e = Arrays.asList(true, false, true);

        String jsonAtoB = om.writeValueAsString(a1);
        B b1 = JsonMapper.getAvailableFromJson(jsonAtoB, B.class, false, true);

        assertEquals("false",                        b1.a);
        assertEquals(1,                              b1.b);   // true  → 1
        assertEquals(9824598L,                       b1.c);
        assertEquals(984,                            b1.d);
        assertEquals(List.of("true","false","true"), b1.e);

        String jsonBtoA = om.writeValueAsString(b1);
        A a2 = JsonMapper.getAvailableFromJson(jsonBtoA, A.class, false, true);

        assertFalse(a2.a);
        assertEquals(Boolean.TRUE,  a2.b);
        assertEquals(9824598,       a2.c);
        assertEquals(984L,          a2.d);
    }

    @Test
    void overrideFalseDoesNotOverwriteExistingValue() {
        Auftraggeber existing = new Auftraggeber();
        existing.vorname = "ExistingName";

        String json = "{\"vorname\":\"NewName\",\"nachname\":\"Schmidt\"}";
        JsonMapper.getAvailableFromJson(json, existing, false, false);

        assertEquals("ExistingName", existing.vorname); // must not be overwritten
        assertEquals("Schmidt",      existing.nachname);
    }

    @Test
    void overrideTrueOverwritesExistingValue() {
        Auftraggeber existing = new Auftraggeber();
        existing.vorname = "ExistingName";

        String json = "{\"vorname\":\"NewName\",\"nachname\":\"Schmidt\"}";
        JsonMapper.getAvailableFromJson(json, existing, true, false);

        assertEquals("NewName", existing.vorname); // must be overwritten
    }

    @Test
    void lenientFalseSkipsTypeMismatch() {
        // boolean value in JSON, String field in target – strict mode must skip
        String json = "{\"a\":false}";
        B b = JsonMapper.getAvailableFromJson(json, B.class, false, false);
        assertNull(b.a); // String field must not be filled from a boolean
    }

    @Test
    void lenientTrueConvertsTypeMismatch() {
        String json = "{\"a\":false}";
        B b = JsonMapper.getAvailableFromJson(json, B.class, false, true);
        assertEquals("false", b.a); // boolean → String conversion
    }

    @Test
    void collectionMapping() {
        String json = "{\"e\":[true,false,true]}";
        A a = JsonMapper.getAvailableFromJson(json, A.class, false, false);

        assertNotNull(a.e);
        assertEquals(3,     a.e.size());
        assertTrue(a.e.get(0));
        assertFalse(a.e.get(1));
        assertTrue(a.e.get(2));
    }

    @Test
    void unknownFieldsInJsonAreIgnored() {
        String json = "{\"vorname\":\"Max\",\"unknownField\":\"ignored\","
                    + "\"anotherUnknown\":42}";
        assertDoesNotThrow(() ->
            JsonMapper.getAvailableFromJson(json, Auftraggeber.class, false, false));
    }

    @Test
    void missingFieldsInJsonLeaveTargetNull() {
        String json = "{\"vorname\":\"Max\"}";
        Auftraggeber a = JsonMapper.getAvailableFromJson(json, Auftraggeber.class, false, false);
        assertNull(a.nachname);
        assertNull(a.betriebsstellenname);
    }

    @Test
    void nestedObjectMappedFromFlatSource() {
        // JSON has betriebsstellenname at top level; target has it nested in Betriebsstelle
        String json = "{\"personalnummer\":7,\"vorname\":\"Tom\","
                    + "\"nachname\":\"Müller\",\"betriebsstellenname\":\"Bremen\","
                    + "\"standarddrucker\":\"Canon\",\"drucker\":\"Canon\"}";

        Mitarbeiter m = JsonMapper.getAvailableFromJson(json, Mitarbeiter.class, false, false);

        assertEquals("Tom",    m.vorname);
        // betriebsstelle sub-object created; its betriebsstellenname found via DFS
        assertNotNull(m.betriebsstelle);
        assertEquals("Bremen", m.betriebsstelle.betriebsstellenname);
    }
}
