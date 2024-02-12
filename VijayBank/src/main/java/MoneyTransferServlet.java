

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/MoneyTransferServlet")
public class MoneyTransferServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
    
    public MoneyTransferServlet() {
        super();
        
    }

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		
		
		
		int src=Integer.parseInt(request.getParameter("accountnumber"));
		int amt=Integer.parseInt(request.getParameter("amount"));
		int dest=Integer.parseInt(request.getParameter("accountnumber"));
		
		PrintWriter pw=response.getWriter();
		
		 Connection con=null;
//		 con.setAutoCommit(false);
		 
		 try
		 {
			 
			   // con.setAutoCommit(true);
			     Class.forName("oracle.jdbc.driver.OracleDriver"); 
				 String url="jdbc:oracle:thin:@localhost:1521:xe";
				 con=DriverManager.getConnection(url,"system","056679");
				 
				 String sql1="select balance from Account where accountnumber=?";
				 
				 PreparedStatement ps1= con.prepareStatement(sql1);
				
				 ps1.setInt(1, src);
			 
				 ResultSet rs=ps1.executeQuery();
				 if(rs.next())
				 {
					 int balance=rs.getInt(1);
					 if(balance>=amt)
					 {
						 String sql2="Update Account set balance=balance-? where accountnumber=?";
						 PreparedStatement ps2= con.prepareStatement(sql2);
						 ps2.setInt(1, amt);
						 ps2.setInt(1, src);
						 
						 ps2.executeUpdate();
						 
						 pw.println("Account Deducted from Sorce Account");
						
						  
						 String sql3="Update Account set balance=balance+? where accountnumber=?";
						 PreparedStatement ps3= con.prepareStatement(sql3);
						 ps3.setInt(1, amt);
						 ps3.setInt(2, src);
						 
						 int count=ps3.executeUpdate();
						 if(count>0)
						 {
							 pw.println("Ammount transfer successfully");
							  con.commit();
//							  response.setContentType("text/html");
//								RequestDispatcher rd=request.getRequestDispatcher("Success.html");
//								rd.include(request, response);
 
						 }
						 else
						 {
							 pw.println("Destination account Missing");
							 con.rollback();
//							  response.setContentType("text/html");
//								RequestDispatcher rd=request.getRequestDispatcher("Error1.html");
//								rd.include(request, response); 
						 }
					 }
					 else
					 {
						 pw.println("Insuffient in source Account");
//						 response.setContentType("text/html");
//							RequestDispatcher rd=request.getRequestDispatcher("Error2.html");
//							rd.include(request, response); 
						 
					 }
				 }
				 else
				 {
					 pw.println("Source account not valid");
//					 response.setContentType("text/html");
//						RequestDispatcher rd=request.getRequestDispatcher("Error3.html");
//						rd.include(request, response); 
				 }
				 
			 
		 }
		 catch(Exception e)
		 {
			 pw.println("Exception:"+e.getMessage());
		 }
		 finally
		 {
			 try {
				con.close();
			} catch (SQLException e) {
				
				e.printStackTrace();
			}
		 }
		
		
		
		
	}

}
