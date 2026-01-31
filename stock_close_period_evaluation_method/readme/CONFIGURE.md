La chiusura di magazzino è accessibile dal menu:

![Menu chiusura](../static/description/menu_chiusura.png)

Qui è possibile creare la chiusura dalla prima voce:

![Crea chiusura](../static/description/crea_chiusura.png)

In questa maschera è necessario inserire il nome, la data in cui verrà
calcolata la giacenza dei prodotti e il metodo di valuzione a scelta tra
i seguenti:

1.  in base alla categoria del prodotto
2.  in base al costo medio di acquisto
3.  in base al costo del prodotto
4.  in base al FIFO continuo
5.  in base al FIFO a scatti
6.  in base al LIFO continuo
7.  in base al LIFO a scatti

È possibile impostare di ignorare le quantità negative a magazzino, nel
caso sia necessario (tenendo conto che vanno comunque sistemate):

![Ignora quantità negative](../static/description/ignora_negativi.png)

Si può quindi avviare la procedura con il seguente bottone, che calcola
le giacenze dei prodotti alla data indicata:

![Inizia](../static/description/inizia.png)

Il passaggio successivo è avviare il calcolo dei prodotti acquistati (ci
metterà un po' di tempo, quindi lasciarlo lavorare). Il calcolo del
costo prende il prezzo dalla fattura collegata all'ordine, se esiste ed
è validata, altrimenti dall'ordine, infine dal prodotto.

![Calcola acquisti](../static/description/calcola_acquisti.png)

Nel caso sia installata l'app produzione, avviare il calcolo dei
manufatti con questo bottone (anche questo impiegherà del tempo):

![Calcola produzione](../static/description/calcola_produzione.png)

Alla fine dei calcoli saranno marcati i flag seguenti, per indicare che
sono stati eseguiti correttamente:

![Flag](../static/description/flag.png)

Si può quindi validare la chiusura (che si può sempre riportare a bozza
e rifare) con questo bottone, che provvede anche ad eliminare le righe
con quantità negativa o pari a zero:

![Valida](../static/description/valida.png)

È infine possibile esportare un report in xlsx:

![Esporta](../static/description/esporta.png)
