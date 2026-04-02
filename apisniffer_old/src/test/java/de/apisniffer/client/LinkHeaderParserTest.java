package de.apisniffer.client;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class LinkHeaderParserTest {

    /** Exact header from the article (Listing 1). */
    private static final String FULL_HEADER =
            "<http://server/service/mitarbeiter>; rel=\"info\"; "
            + "type=\"text/html\"; title=\"Einstiegslinks\"; verb=\"GET,OPTIONS\","
            + " <http://server/service/mitarbeiter/mitarbeiter>; rel=\"all\"; "
            + "type=\"application/json\"; title=\"Angemeldete Mitarbeiter\"; verb=\"GET\","
            + " <http://server/service/mitarbeiter/mitarbeiter?name=>; rel=\"suche\"; "
            + "type=\"application/json\"; title=\"Mitarbeitersuche\"; verb=\"GET\","
            + " <http://server/service/mitarbeiter/anmeldung>; rel=\"new\"; "
            + "type=\"application/json\"; title=\"Mitarbeiterlogin\"; verb=\"POST\"";

    @Test
    void parsesAllFourLinksFromArticleExample() {
        Map<LinkHeaderType, Link> links = LinkHeaderParser.parse(FULL_HEADER);

        assertEquals(4, links.size());
        assertNotNull(links.get(LinkHeaderType.INFO));
        assertNotNull(links.get(LinkHeaderType.ALL));
        assertNotNull(links.get(LinkHeaderType.SUCHE));
        assertNotNull(links.get(LinkHeaderType.NEW));
    }

    @Test
    void allLinkHasCorrectAttributes() {
        Map<LinkHeaderType, Link> links = LinkHeaderParser.parse(FULL_HEADER);
        Link all = links.get(LinkHeaderType.ALL);

        assertEquals("http://server/service/mitarbeiter/mitarbeiter", all.getHref());
        assertEquals("application/json", all.getType());
        assertEquals("Angemeldete Mitarbeiter", all.getTitle());
        assertEquals("GET", all.getVerb());
        assertEquals(LinkHeaderType.ALL, all.getRel());
    }

    @Test
    void newLinkHasPostVerb() {
        Map<LinkHeaderType, Link> links = LinkHeaderParser.parse(FULL_HEADER);
        assertEquals("POST", links.get(LinkHeaderType.NEW).getVerb());
    }

    @Test
    void nullHeaderReturnsEmptyMap() {
        assertTrue(LinkHeaderParser.parse(null).isEmpty());
    }

    @Test
    void blankHeaderReturnsEmptyMap() {
        assertTrue(LinkHeaderParser.parse("   ").isEmpty());
    }

    @Test
    void unknownRelTypeIsIgnored() {
        String header = "<http://example.com/foo>; rel=\"unknown\"; "
                      + "type=\"application/json\"; title=\"X\"; verb=\"GET\"";
        assertTrue(LinkHeaderParser.parse(header).isEmpty());
    }

    @Test
    void singleLinkParsedCorrectly() {
        String header = "<http://example.com/items>; rel=\"all\"; "
                      + "type=\"application/json\"; title=\"Items\"; verb=\"GET\"";
        Map<LinkHeaderType, Link> links = LinkHeaderParser.parse(header);

        assertEquals(1, links.size());
        assertEquals("http://example.com/items", links.get(LinkHeaderType.ALL).getHref());
    }
}
