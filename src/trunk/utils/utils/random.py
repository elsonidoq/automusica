def convex_combination(distr1, distr2, factor=0.5):
    """
    params:
      distr1 :: [(thing, float)]
      distr2 :: [(thing, float)]
      factor :: float

    pre:
      sum(i[1] for i in distr1) == 1
      sum(i[1] for i in distr2) == 1
      factor <=1
      factor >=0
      distr1 y distr2 estan ordenadas

    returns:
      new_distr :: [(thing, float)]
      new_distr es la combinacion convexa entre distr1 y distr2
      new_distr esta ordenada 
    """
    new_distr= []
    i=0
    j=0
    while i<len(distr1) or j < len(distr2):
        if i<len(distr1) and j < len(distr2):
            thing1, prob1= distr1[i]
            thing2, prob2= distr2[j]
            if thing1 == thing2:
                new_distr.append((thing1, (prob1+prob2)*factor))
                i+=1
                j+=1
            elif thing1 > thing2:
                new_distr.append((thing2, prob2*factor))
                j+=1
            else:
                new_distr.append((thing1, prob1*factor))
                i+=1
        elif i < len(distr1):
            thing1, prob1= distr1[i]
            new_distr.append((thing1, prob1*factor))
            i+=1
        else:
            thing2, prob2= distr2[j]
            new_distr.append((thing2, prob2*factor))
            j+=1

    return new_distr
