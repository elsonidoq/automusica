from electrozart.algorithms import CacheAlgorithm, needs


class RythmCacheAlgorithm(CacheAlgorithm):
    @needs('now')
    def generate_list(self, input, result, prev_notes):
        if self.input_key in input:
            cache_key= input[self.input_key]
            if cache_key not in self.cache:
                answer= self.generate_list_orig(input, result, prev_notes)
                self.cache[cache_key]= (answer, input.now)
            else:
                old_answer, old_start= self.cache[cache_key]
                offset= input.now - old_start
                new_answer= []
                for old_input, old_result in old_answer:
                    # copio los viejos input y result y le piso con las cosas
                    # de los nuevos input y result
                    new_input= old_input.copy()
                    new_input.update(input)

                    new_result= old_result.copy()
                    new_result.update(result)
                    new_result.start+= offset

                    new_answer.append((new_input, new_result))

                answer= new_answer

        else:
            answer= self.generate_list_orig(input, result, prev_notes)

        return answer[:]
 
