import java.lang.Math;

public static void main (String args[]){
    double mean = 0;
    int count = 1000;
	int total = 0;
	for (i = 0; i < count; ++i){
		total += takeSeat(25);
	}
	mean = total / count;
}

public static double takeSeat(int seats){
	int[] occupied = new int[seats];
	int taken = 0;
	int choice = 0;
	int counter = 0;
	
	while (taken < seats){
		
		choice = randomNumber(0, seats-1);

		if (choice == 0 && occupied[1] != 2) {
			occupied[0] = 2;
			occupied[1] = 1;
			taken += 2;
			counter++;
		} else if (choice == seat && occupied[seat-1]){
			occupied[seat-1] = 2;
			occupied[seat-2] = 1;
			taken += 2;
			counter++;
		} else if (occupied[choice-1] != 2 && occupied[choice+1] != 2){
			occupied[choice] = 2;
			occupied[choice-1] = 1;
			occupied[choice+1] = 1;
			taken += 3;
			counter++;
		}
	}
	
	return (double) counter/seats;
}

    // give a random number from min to max
    public static int randomNumber(int min, int max) {
        Random rand = new Random();
        int randomNumber = rand.nextInt(max - min + 1) + min;
        return randomNumber;
    }