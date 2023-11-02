import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

//wenn die vocab datei geaendert wird und zwischendrin eingefuegt wird, crasht die freq liste

public class Vocabs 
{
	static Scanner s;
	static BufferedReader br;
	
    static ArrayList<String[]> content;
    
    static int score = 0;
    static String result = "";
    
	static int globalScore;
	static int gamesPlayed;
	static ArrayList<Integer> frequency = new ArrayList<>();
	static ArrayList<Integer> reverseFrequency = new ArrayList<>();
	
	static String inputVocabs = "D:\\Dokumente\\Dateien\\Uni\\Eclipse\\Sem5_Uebungen\\Spanisch\\vocabs.md";
	static String scoreFile = "D:\\Dokumente\\Dateien\\Uni\\Eclipse\\Sem5_Uebungen\\Spanisch\\score.txt";
	static String language = "español";

	static boolean askBothDirections = false;
    
    public static void main(String[] args) throws IOException, InterruptedException
    {
    	if(args.length > 0)
    		language = args[0];
    	if(args.length > 1)
    		inputVocabs = args[1];
    	if(args.length > 2)
    		scoreFile = args[2];
    		
        prepareGame();

        start();

        updateStats();
    }   
    
//    public static void test() throws IOException, InterruptedException
//    {
//    	System.out.println(System.getProperty("file.encoding"));
//    }
    
    private static void prepareGame()
    {
    	readWords();
    	List<String[]> reverseContent = new ArrayList<>();
    	for(String[] e: content)
    	{
    		String[] copy = Arrays.copyOf(e, e.length);
    		copy[0] = e[1];
    		copy[1] = e[0];
    		reverseContent.add(copy);
    	}
    	getStats();
    }
    
    private static void readWords()
    {
		File f = new File(inputVocabs);
        content = new ArrayList<>();
        
        try(FileReader fr = new FileReader(f, StandardCharsets.UTF_8))
        {
            BufferedReader reader = new BufferedReader(fr);

            String currLine = reader.readLine();
            while(currLine != null)
            {
            	String[] currCols = currLine.substring(1).split("\\|");
                content.add(currCols);
                currLine = reader.readLine();
            }
        }
        catch(IOException e)
        {
            e.printStackTrace();
            System.exit(1);
        }
    }

	private static void getStats()
	{
		File file = new File(scoreFile);
		
		try(FileReader fr = new FileReader(file))
		{
			BufferedReader reader = new BufferedReader(fr);
			String line = reader.readLine();
			if(line == null || line.isBlank())
			{
				line = "0 0";
			}
			String[] stats = line.split(" ");
			gamesPlayed = Integer.parseInt(stats[0]);
			globalScore = Integer.parseInt(stats[1]);
			
			line = reader.readLine();
			getFrequencyStats(line, frequency);
			line = reader.readLine();
			getFrequencyStats(line, reverseFrequency);
		}
		catch(IOException e)
		{
			e.printStackTrace();
		}
	}
	
	private static void getFrequencyStats(String line, ArrayList<Integer> list)
	{
		if(line == null || line.isBlank())
		{
			List<Integer> dummy = new ArrayList<>();
			dummy.add(0);
			dummy.add(0);
			line = dummy.toString();
		}
		
		String[] tmp = line.split(",");
		
		for(String f: tmp)
		{
			f = f.replace("[", "").replace("]", "").trim();
			int i = Integer.parseInt(f);
			list.add(i);
		}
		
		// data: 5,  freq: 1
		if(list.size() < content.size()-2)
		{
			int missing = content.size()-2-list.size();
			for (int i=0; i<missing; i++)
			{
				list.add(0);
			}
		}
	}

    private static void start() throws IOException
    {
    	print('#');
    	print('-');
        System.out.println(language.toUpperCase() + " VOCAB TEST:");
       
        s = new Scanner(System.in, StandardCharsets.ISO_8859_1);
        
        for(int i=0; i<3; i++)
        {
        	print('-');
        	ask();
        }
		gamesPlayed++;
    	globalScore += score;
    	float average = (int)(((double)globalScore / gamesPlayed)*100)/100.0F;
        
        s.close();
        
        print('-');
        System.out.println("Your Score: " + score + " " + result);
        print('-');
        print('#');
        print('-');
		System.out.println("New Global Score: " + globalScore);
		System.out.println("Games played: " + gamesPlayed);
		System.out.println("Average Score: " + average);
		print('-');
		print('#');
	}
    
    private static void ask() throws IOException
    {
    	IndicesTriple indices = getSuitableRandom();
    	List<Integer> freqList = indices.question == 0 ? frequency : reverseFrequency;
    	String question = content.get(indices.row)[indices.question];
    	List<String> solution = prepareSolution(indices);
    	
    	System.out.println("### " + question + " (" + freqList.get(indices.row-2) + ")");
    	
    	for(int i=0; i<3; i++)
    	{
    		List<String> answer = new ArrayList<String>();
			String in = s.nextLine();

			if(in == null || in.isBlank())
			{
				i--;
				s.reset();
				System.out.println("--> ?   [try again]");
				continue;
			}

    		String[] tmp = in.split(",");
    		for(String a: tmp)
    		{	
    			answer.add(sanitizeString(a));
    		}
    	
    		if(answer.containsAll(solution))
        	{
        		switch(i)
        		{
        		case 0: 
        			result += "#"; 
        			score += 3;
        			freqList.set(indices.row-2,freqList.get(indices.row-2)+1); 
        			break;
        		case 1: 
        			result += "*"; 
        			score += 2; 
        			break;
        		case 2: 
        			result += "."; 
        			score += 1; 
        			break;
        		}
        		
    			System.out.println("--> V   " + solution.toString());
        		break;
        	}
    		
    		
    		String wrong;
    		if(i==0)
    		{
    			wrong = "--> X   [try again]";
    		}
    		else if(i==1)
    		{
    			wrong="--> XX  [try again]";
    		}
    		else
    		{
    			wrong="--> XXX " + solution;
    			result += "-";
    		}
    		
    		System.out.println(wrong);
    	}
    }
    
    private static List<String> prepareSolution(IndicesTriple indices)
    {
    	List<String> solution = new ArrayList<String>();
    	solution.add(content.get(indices.row)[indices.answer]);
    	
    	if(solution.get(0).contains(","))
    	{
    		String[] tmp = solution.get(0).split(",");
    		solution.clear();
    		for(String s: tmp)
    		{
    			solution.add(sanitizeString(s));
    		}
    	}
    	else
    	{
    		String s = sanitizeString(solution.get(0));
			solution.clear();
			solution.add(s);
    	}
    	return solution;
    }
    
    private static String sanitizeString(String s)
    {
    	s = s.trim().toLowerCase();
    	if(language.equals("english"))
    	{
    		if(s.charAt(0) == 't' && s.charAt(1) == 'o' && s.charAt(2) == ' ')
    		{
    			s = s.substring(3);
    		}
    	}
		return s;
    }
    
    // Zufallszahl [2,letztes Element]
    private static IndicesTriple getSuitableRandom()
    {
		int maxFreqFreq = frequency.stream().mapToInt(i -> (int) i).max().getAsInt();
		int maxFreqRevFreq = reverseFrequency.stream().mapToInt(i -> (int) i).max().getAsInt();
		int minFreqFreq = frequency.stream().mapToInt(i -> (int) i).min().getAsInt();
		int minFreqRevFreq = reverseFrequency.stream().mapToInt(i -> (int) i).min().getAsInt();
    	int max = askBothDirections ? Integer.max(maxFreqFreq, maxFreqRevFreq) : maxFreqFreq;
    	int min = askBothDirections ? Integer.min(minFreqFreq, minFreqRevFreq) : minFreqFreq;
    	
    	int row;
    	int questionIndex;
    	do
    	{
    		row = (int)(Math.random()*(content.size()-2)) +2;
    		questionIndex = askBothDirections ? (int)(Math.random()*2) : 0;
    	}
    	while(max!=0 && (questionIndex == 0 ? frequency.get(row-2)!=min : reverseFrequency.get(row-2)!=min));
    	
    	return new IndicesTriple(row, questionIndex, questionIndex == 0 ? 1 : 0);
    }

	private static void updateStats()
	{
		File f = new File(scoreFile);
		
		try(FileWriter fw = new FileWriter(f, false))
		{
			BufferedWriter writer = new BufferedWriter(fw);
			
			writer.write(gamesPlayed+" "+globalScore+"\n"+frequency.toString()+"\n"+reverseFrequency.toString());
			writer.close();
		}
		catch(IOException e)
		{
			e.printStackTrace();
		}
	}
	
	private static void print(char c)
	{
		switch (c)
		{
		case '-': System.out.println("----------------------------------------------"); break;
		case '#': System.out.println("##############################################"); break;
		}
	}
}

class IndicesTriple
{
	int row;
	int question;
	int answer;
	
	public IndicesTriple(int row, int question, int answer)
	{
		this.row = row;
		this.question = question;
		this.answer = answer;
	}	
}
