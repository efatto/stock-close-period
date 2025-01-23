La chiusura di magazzino è accessibile dal menu:

.. image:: ../static/description/menu_chiusura.png
    :alt: Menu chiusura

Qui è possibile creare la chiusura dalla prima voce:

.. image:: ../static/description/crea_chiusura.png
    :alt: Crea chiusura

In questa maschera è necessario inserire il nome, la data in cui verrà calcolata la giacenza dei prodotti e il metodo di valuzione a scelta tra i seguenti:

.. image:: ../static/description/metodi_valutazione.png
    :alt: Metodi valutazione

È possibile impostare di ignorare le quantità negative a magazzino, nel caso sia necessario (tenendo conto che vanno comunque sistemate):

.. image:: ../static/description/ignora_negativi.png
    :alt: Ignora quantità negative

Si può quindi avviare la procedura con il seguente bottone, che calcola le giacenze dei prodotti alla data indicata:

.. image:: ../static/description/inizia.png
    :alt: Inizia

Il passaggio successivo è avviare il calcolo dei prodotti acquistati (ci metterà un po' di tempo, quindi lasciarlo lavorare). Il calcolo del costo prende il prezzo dalla fattura collegata all'ordine, se esiste ed è validata, altrimenti dall'ordine, infine dal prodotto.

.. image:: ../static/description/calcola_acquisti.png
    :alt: Calcola acquisti

Nel caso sia installata l'app produzione, avviare il calcolo dei manufatti con questo bottone (anche questo impiegherà del tempo):

.. image:: ../static/description/calcola_produzione.png
    :alt: Calcola produzione

Alla fine dei calcoli saranno marcati i flag seguenti, per indicare che sono stati eseguiti correttamente:

.. image:: ../static/description/flag.png
    :alt: Flag

Si può quindi validare la chiusura (che si può sempre riportare a bozza e rifare) con questo bottone, che provvede anche ad eliminare le righe con quantità negativa o pari a zero:

.. image:: ../static/description/valida.png
    :alt: Valida

È infine possibile esportare un report in xlsx:

.. image:: ../static/description/esporta.png
    :alt: Esporta
